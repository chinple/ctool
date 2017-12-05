'''
Created on 2013-4-1

@author: miansheng.yims
'''

import re
from cserver import cloudModule, cprop
from libs.objop import ObjOperation
from server.cclient import  curlCservice, curl
from libs.parser import toJsonObj
import time
from db.filedb import FileDataBase
from threading import Thread
from libs.syslog import slog

class CserviceDataApi:
    def __init__(self):
        dataPath = cprop.getVal("ctool", "dataPath", "./webs/data")
        self.datas = FileDataBase(dataPath, keyDefines={'a':'json', 't':'equal'})
        self.servers = FileDataBase(dataPath, keyDefines={ 'a':'equal'})

    def saveServer(self, hostport=None, serverName=None, serverType=None):
        return self.servers.saveRecord("ctool-server", {'a':hostport, 'n':serverName, 't':serverType}, True, True)
    def getServer(self,):
        return self.servers.getRecord("ctool-server")

    def saveInfData(self, infName, argInfo, requestArgs, argRely=None, timeMark=None, respData=None):
        if timeMark is None:
            timeMark = str(time.time())

        return self.datas.saveRecord(infName, {"a":requestArgs, "i":argInfo,
            "r":argRely, "d":respData, "t":str(timeMark)}, isUpdate=True, isFlush=True)

    def getInfData(self, infName, infCond=None):
        return self.datas.getRecord(infName, infCond)

    def deleteInfData(self, infName, timeMark):
        return self.datas.removeRecord(infName, {'t':str(timeMark)})

@cloudModule()
class CServiceTool:
    def __init__(self):
        self.dapi = CserviceDataApi()

# Servers
    def registServer(self, hostport, serverName=None, serverType=None, initMethods=None):
        if hostport is not None and hostport != ""and not hostport.startswith("127"):
            slog.info("register: %s %s with: %s" % (hostport, serverName, initMethods))
            self.dapi.saveServer(hostport, serverName, serverType)
        if initMethods is not None and initMethods != "":
            Thread(target=self.__initService, args=(hostport, initMethods)).start()

    def __initService(self, hostport, initMethods):
        time.sleep(3)
        for infName in initMethods.split(","):
            resps = []
            for inf in self.searchInfData(infName): 
                requestArgs = inf['a']
                try:
                    resp = self.doInfRequest(hostport, infName, requestArgs)
                except Exception as ex:
                    resp = str(ex)
                resps.append(resp)
            slog.info("Init method %s %s: %s" % (hostport, infName, resps))

    def getServer(self):
        return self.dapi.getServer()

    def _getServerAddress(self, serverName):
        serverName = str(serverName).strip().lower()
        for s in self.infServers.keys():
            if serverName == str(self.infServers[s]).lower():
                return s
        return serverName

    def getService(self, hostPort):
        return curlCservice(hostPort, "param", isGetInfo=True, connTimeout=1)

# Data
    def addInfData(self, infName, requestArgs, respData, argInfo, argRely, ignoreArgs=[], timeMark=None):
        requestArgs = toJsonObj(requestArgs)
        ignoreArgs = toJsonObj(ignoreArgs)
        argRely = toJsonObj(argRely)

        return self.dapi.saveInfData(infName, argInfo, requestArgs, argRely, timeMark)

    def searchInfData(self, infName, infCond={}):
        infCond = toJsonObj(infCond)
        return self.dapi.getInfData(infName, infCond)

    def deleteInfData(self, infName, timeMark):
        return self.dapi.deleteInfData(infName, timeMark)

    def moveInfData(self, infName, timeMark1, timeMark2):
        return False

# Request
    def getInfRelys(self, infRely):
        infRely = toJsonObj(infRely)
        infBefores = []
#         infInfo = infRely
#         repeatInfo = []
#         while infInfo is not None:
#             infName = infInfo["before"]
#             befArg = infInfo["beforeArg"]
# 
#             infData = self.__searchInfDataArg__(infName, befArg)
#             if infData == None:
#                 break
#             else:
#                 infInfo = infData['i']
#                 repeatMark = "%s%s" % (infName, infInfo)
#                 if repeatInfo.__contains__(repeatMark):
#                     break
#                 else:
#                     repeatInfo.append(repeatMark)
#                 infBefores.insert(0, [infName, infData['a'], infInfo])
#                 infInfo = ObjOperation.tryGetVal(infData, 'r', None)

#         infName = infRely["after"]
        infAfter = None
#         infData = self.__searchInfDataArg__(infName, infRely["afterArg"])
#         if infData is not None:
#             infAfter = [infName, infData['a'], infData['i']]
        return infBefores, infAfter

    def doInfRequest(self, hostPort, infName, requestArgs, replaceProp=None, isHostName=False):
        infPath = infName.replace(".", "/")
        requestArgs = toJsonObj(requestArgs)

        if replaceProp is not None and replaceProp != "" and requestArgs != "":
            try:
                for argName in requestArgs.keys():
                    if replaceProp.__contains__(argName):
                        originVal = requestArgs[argName]
                        requestArgs[argName] = self.replaceValues.TryGet(originVal, originVal)
                requestArgs = requestArgs.__str__(0, True)
            except:pass

        return curlCservice(self._getServerAddress(hostPort) if isHostName else hostPort, infPath, isCheckResp=True, **requestArgs)

# Test
    def executeInfTest(self, hostPort, infName, dataIndex, inProp="", outProp="", replaceProp=None, isDirectReturn=False):
        infCase = self.__getInfData__(infName)[int(dataIndex)]
        infRet = self.doInfRequest(hostPort, infName, infCase['a'], replaceProp)

        if str(isDirectReturn).lower() == "true":
            return infRet

        try:
            resp = ObjOperation.jsonEqual(toJsonObj(infCase['d']), infRet,
                    isAddEqInfo=True, isCmpHandler=lambda key, keyPath:self.__isNeedCheck__(key, keyPath, inProp, outProp))
        except:
            if infCase['d'] == infRet:
                resp = [0, str(infRet)]
            else:
                resp = [1, str(infRet)]

        return list(resp)

    def __isNeedCheck__(self, key, keyPath, inProp, outProp):
        if keyPath is not None:
            if inProp is not None and inProp != "":
                if re.match(inProp, keyPath) is not None:
                    return True
                else:
                    return False
            if outProp is not None and outProp != "":
                if re.match(outProp, keyPath) is not None:
                    return False
        return True

@cloudModule()
class LogServerTool:
    def statFolder(self, hostport, path):
        return toJsonObj(curl("%s/file/%s?type=stat" % (hostport, path)))
    def readFile(self, hostport, path, limit=10240):
        return curl("%s/file/%s?limit=%s" % (hostport, path, limit))

@cloudModule(imports="CServiceTool.dapi")
class ProxyMockTool:
    dapi = None

    def getProxys(self, mockaddr, proxyName):
        if proxyName == "" or proxyName.strip() == "":proxyName = None
        proxy = self.dapi.getInfData('LogHttpProxy.reloadProxyConfig')
        ps = []
        for p in proxy:
            if proxyName is None or p['i'].__contains__(proxyName) or p['a']['proxyConfig'].__contains__(proxyName):
                ps.append({'i':p['i'], 'p':p['a']['proxyConfig'], 't':p['t']})
        return ps

    def addProxy(self, mockaddr, info, proxy, timeMark=None):
        curlCservice(mockaddr, 'LogHttpProxy/reloadProxyConfig', isCheckResp=True, proxyConfig=proxy)
        return self.dapi.saveInfData("LogHttpProxy.reloadProxyConfig", info, {'proxyConfig':proxy}, timeMark=timeMark)

    def deleteProxy(self, mockaddr, timeMark):
        return self.dapi.deleteInfData("LogHttpProxy.reloadProxyConfig", timeMark)

# mock
    def getUrlMock(self, mockaddr, mockurl=None):
        if mockurl == "" or mockurl.strip() == "":mockurl = None
        mock = self.dapi.getInfData("LogHttpProxy.addUrlMock")
        ms = []
        for p in mock:
            try:
                if mockurl is None or p['i'].__contains__(mockurl) or p['a']['url'].__contains__(mockurl):
                    ms.append({'i':p['i'], 't':p['t'], 'url':p['a']['url'], 'resp':p['a']['resp'], 'param':p['a']['param'], 'isdelete':p['a']['isdelete']})
            except:
                self.deleteUrlMock(mockaddr, p['t'], None, "true")
        return ms

    def addUrlMock(self, mockaddr, info, mockurl, mockparam, mockresp, timeMark=None):
        curlCservice(mockaddr, 'LogHttpProxy/addUrlMock', isCheckResp=True,
            url=mockurl, param=mockparam, resp=mockresp)
        return self.dapi.saveInfData("LogHttpProxy.addUrlMock", info, {'url':mockurl,
            'resp':mockresp, 'param':mockparam, "isdelete":"false"}, timeMark=timeMark)

    def deleteUrlMock(self, mockaddr, timeMark, url, isdelete):
        curlCservice(mockaddr, 'LogHttpProxy/addUrlMock', isCheckResp=True,
            url=url, param="", resp="", isdelete="true")
        if isdelete == "true":
            return self.dapi.deleteInfData("LogHttpProxy.addUrlMock", timeMark)
        else:
            mock = self.dapi.getInfData("LogHttpProxy.addUrlMock", {'t':timeMark})
            mock[0]['a']['isdelete'] = 'true'

if __name__ == "__main__":
    from cserver import servering
    servering("-p 8089 -f webs  -m CToolPlatform.html ")
