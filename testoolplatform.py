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

class CserviceDataApi:
    def __init__(self):
        dataPath = cprop.getVal("ctool", "dataPath", "./webs/data")
        self.datas = FileDataBase(dataPath, keyDefines={'a':'json', 't':'equal'})
        self.servers = FileDataBase(dataPath, keyDefines={ 'a':'equal'})

    def saveServer(self, hostport=None, serverName=None, serverType=None):
        return self.servers.saveRecord("ctool-server", {'a':hostport, 'n':serverName, 't':serverType}, True, True)
    def getServer(self,):
        return self.servers.getRecord("ctool-server")

    def saveInfData(self, infName, argInfo, requestArgs, argRely, timeMark, respData=None):
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
    def RegistServer(self, hostport=None, serverName=None, serverType=None):
        if hostport != None and hostport != ""and not hostport.startswith("127"):
            self.dapi.saveServer(hostport, serverName, serverType)
        return self.dapi.getServer()

    def GetService(self, hostPort):
        return curlCservice(hostPort, "param", isGetInfo=True, isCheckResp=True)

    def GetServerAddress(self, serverName):
        serverName = str(serverName).strip().lower()
        for s in self.infServers.keys():
            if serverName == str(self.infServers[s]).lower():
                return s
        return serverName

# Data
    def AddInfData(self, infName, requestArgs, respData, argInfo, argRely, ignoreArgs=[], timeMark=None):
        requestArgs = toJsonObj(requestArgs)
        ignoreArgs = toJsonObj(ignoreArgs)
        argRely = toJsonObj(argRely)

        if timeMark is None:
            timeMark = str(time.time())
        return self.dapi.saveInfData(infName, argInfo, requestArgs, argRely, timeMark)

    def SearchInfData(self, infName, infCond={}):
        infCond = toJsonObj(infCond)
        return self.dapi.getInfData(infName, infCond)

    def DeleteInfData(self, infName, timeMark):
        return self.dapi.deleteInfData(infName, timeMark)

    def MoveInfData(self, infName, timeMark1, timeMark2):
        return False

# Request
    def GetInfRelys(self, infRely):
        infRely = toJsonObj(infRely)
        infBefores = []
#         infInfo = infRely
#         repeatInfo = []
#         while infInfo != None:
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
#         if infData != None:
#             infAfter = [infName, infData['a'], infData['i']]
        return infBefores, infAfter

    def DoInfRequest(self, hostPort, infName, requestArgs, replaceProp=None, isHostName=False):
        infPath = infName.replace(".", "/")
        requestArgs = toJsonObj(requestArgs)

        if replaceProp != None and replaceProp != "" and requestArgs != "":
            try:
                for argName in requestArgs.keys():
                    if replaceProp.__contains__(argName):
                        originVal = requestArgs[argName]
                        requestArgs[argName] = self.replaceValues.TryGet(originVal, originVal)
                requestArgs = requestArgs.__str__(0, True)
            except:pass

        return curlCservice(self.GetServerAddress(hostPort) if isHostName else hostPort, infPath, isCheckResp=True, **requestArgs)

# Test
    def ExecuteInfTest(self, hostPort, infName, dataIndex, inProp="", outProp="", replaceProp=None, isDirectReturn=False):
        infCase = self.__getInfData__(infName)[int(dataIndex)]
        infRet = self.DoInfRequest(hostPort, infName, infCase['a'], replaceProp)

        if str(isDirectReturn).lower() == "true":
            return infRet

        try:
            resp = ObjOperation.jsonEqual(toJsonObj(infCase['d']), infRet,
                    isAddEqInfo=True, isCmpHandler=lambda key, keyPath:self.__IsNeedCheck__(key, keyPath, inProp, outProp))
        except:
            if infCase['d'] == infRet:
                resp = [0, str(infRet)]
            else:
                resp = [1, str(infRet)]

        return list(resp)

    def __IsNeedCheck__(self, key, keyPath, inProp, outProp):
        if keyPath != None:
            if inProp != None and inProp != "":
                if re.match(inProp, keyPath) != None:
                    return True
                else:
                    return False
            if outProp != None and outProp != "":
                if re.match(outProp, keyPath) != None:
                    return False
        return True

@cloudModule()
class LogServerTool:
    def statFolder(self, hostport, path):
        return toJsonObj(curl("%s/file/%s?type=stat" % (hostport, path)))
    def readFile(self, hostport, path, limit=10240):
        return curl("%s/file/%s?limit=%s" % (hostport, path, limit))

if __name__ == "__main__":
    from cserver import servering
    servering("-p 8089 -f webs  -m CToolPlatform.html ")
