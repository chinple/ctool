# -*- coding: utf8 -*-
'''
Created on 2016-10-2

@author: chinple
'''
from db.sqllib import Sql
from cserver import cprop, cloudModule
import time
from libs.objop import ObjOperation
from server.csession import LocalMemSessionHandler
from server.chandle import RedirectException, ReturnFileException
from testexecdb import CtestDbOp, EmailReportor
from libs.timmer import TimmerJson

@cloudModule()
class CTestPlanAPi:
    def __init__(self):
        self.dbapi = CtestDbOp()
        self.emailRp = EmailReportor()
        self.enumContainer = {}

    def __setup__(self):
        self._addEnum("planStatus", cprop.getVal("plan", "planStatus"), True)
        self._addEnum("planCaseStatus", cprop.getVal("plan", "planCaseStatus"), True)
        self._addEnum("planPriority", cprop.getVal("plan", "planPriority"), False)
        self._addEnum("planType", cprop.getVal("plan", "planType"), False)

        self._addEnum("deployPhase", "未提测 测试 预发布  正式发布 完成", True)
        self._addEnum("deployStatus", "未部署 部署中 部署成功 部署失败 冻结 完成", True)

    def _addEnum(self, enumname, valstr, isIndexAsValue):
        vals = valstr.split()
        e = []
        for i in range(len(vals)):
            v = vals[i]
            e.append({'v': str(i) if isIndexAsValue else v, 'n': v})
        self.enumContainer[enumname] = e

    def getEnum(self, enumname):
        return self.enumContainer[enumname]

    def deleteCtree(self, nid):
        return self.dbapi.deleteCtree(nid)
    def saveCtree(self, name, fnid=-1, nid=None):
        return self.dbapi.saveCtree(name, fnid, nid)
    def getCtreeRoot(self, fnid=None, name=None, nid=None):
        return self.dbapi.getCtree(fnid, name, nid)

    def saveCtestcase(self, scenario, tags, name, ttype, priority, steps, remark,
            fnid=None, nid1=None, nid2=None, caseid=None, __session__=None):
        owner = __session__['name']
        return self.dbapi.saveCtestcase(scenario, tags, name, ttype, priority, steps, remark, owner, fnid, nid1, nid2, caseid)
    def updateCtestcase(self, caseid, testcase):
        if Sql.isEmpty(caseid):return 0
        tryget = ObjOperation.tryGetVal
        return self.dbapi.saveCtestcase(name=tryget(testcase, 'name', None), priority=tryget(testcase, 'priority', None),
            ttype=tryget(testcase, 'ttype', None), owner=tryget(testcase, 'owner', None),
            remark=tryget(testcase, 'remark', None), caseid=caseid)

    def getCtestcase(self, fnid=None, nid1=None, nid2=None,
            searchKey=None, ttype=None, priority=None, name=None, owner=None, caseid=None):
        return self.dbapi.getCtestcase(fnid, nid1, nid2, searchKey, ttype, priority, name, owner, caseid)

    def getPlancases(self, fnid, planid):
        return self.dbapi.getCtestcase(fnid, planid=planid, isInplan=False)

    def exportCtestcase(self, fnid=None, nid1=None, nid2=None, searchKey=None, ttype=None, priority=None, owner=None, planid=None):
        raise ReturnFileException(self.emailRp.formatTestCase(self.dbapi.getCtestcase(fnid, nid1, nid2, searchKey, ttype, priority, owner=owner, planid=planid, isInplan=True)),
            'text/html')

    def deleteCtestcase(self, caseid):
        return self.dbapi.deleteCtestcase(caseid)

    def saveCtestplan(self, name=None, owner=None, version=None, tags=None, summary=None, issues=None,
            ptype=None, priority=None, status=None, progress=None,
            pstarttime=None, pendtime=None, starttime=None, endtime=None,
            mailto=None, fnid=None, nid1=None, nid2=None, planid=None):
        if Sql.isEmpty(version):version = None
        return self.dbapi.saveCtestplan(name, owner, version, tags, summary, issues, ptype, priority, status, progress, pstarttime, pendtime, starttime, endtime, mailto, fnid, nid1, nid2, planid)

    def updateCtestplan(self, planid, plan):
        if Sql.isEmpty(planid):return 0
        tryget = ObjOperation.tryGetVal
        return self.dbapi.saveCtestplan(owner=tryget(plan, 'owner', None), ptype=tryget(plan, 'ptype', None),
            priority=tryget(plan, 'priority', None), status=tryget(plan, 'status', None), progress=tryget(plan, 'progress', None),
            pendtime=tryget(plan, 'pendtime', None), endtime=tryget(plan, 'endtime', None),
            summary=tryget(plan, 'summary', None), issues=tryget(plan, 'issues', None), planid=planid)

    def getCtestplan(self, fnid=None, nid1=None, nid2=None,
            nameOrTags=None, ptype=None, priority=None, inStatus=None, outStatus=None,
            starttime1=None, starttime2=None, owner=None):
        return self.dbapi.getCtestplan(fnid, nid1, nid2, nameOrTags, ptype, priority, inStatus, outStatus, starttime1, starttime2, owner)

    def getCtestplanById(self, planid):
        if Sql.isEmpty(planid):
            return
        plans = self.dbapi.getCtestplan(planid=planid)
        if len(plans) > 0:
            plan = plans[0]
            planStatus = cprop.getVal('plan', 'planStatus').split()
            plan['planStatus'] = planStatus[plan['status']]
            if plan['version'] is None:plan['version'] = ""
            plan['pstarttime'] = str(plan['pstarttime']).split()[0]
            plan['pendtime'] = str(plan['pendtime']).split()[0]
            plan['starttime'] = str(plan['starttime']).split()[0]
            plan['endtime'] = str(plan['endtime']).split()[0]
            plan['reportTarget'] = cprop.getVal('plan', 'reportTarget').format(**plan)
            plan['reportSummary'] = cprop.getVal('plan', 'reportSummary').format(**plan)
            caseprogress = self.calcPlancaseprogress(planid)
            plan['reportSummary'] = plan['reportSummary'].format(caseprogress=caseprogress)
        return plans

    def getCtestplancasereport(self, planid):
        planCaseRow = cprop.getVal('plan', 'planCaseRow')
        planCaseStatus = cprop.getVal('plan', 'planCaseStatus').split()
        caseinfo = []
        for case in self.dbapi.getPlancase(planid):
            case['result'] = planCaseStatus[case['status']]
            case['remark'] = '' if case['remark'] is None else case['remark']
            caseinfo.append(planCaseRow.format(**case))
        
        return cprop.getVal('plan', 'planCaseTable').format(body="".join(caseinfo))

    def deleteCtestplan(self, planid):
        return  self.dbapi.deleteCtestplan(planid)

    def savePlancase(self, planid, ftags, plancases, __session__):
        for plancase in plancases:
            caseid, scenario, remark, _, name = plancase.split("|,|")  # not use owner
            caseInfo = self.dbapi.getPlancase(planid, caseid)
            if len(caseInfo) > 0:
                case = caseInfo[0]
                plancaseid = case['plancaseid']
                status = case['status']
                owner = case['owner']
                if not Sql.isEmpty(case['remark']):
                    remark = case['remark']
            else:
                plancaseid = None
                status = 0
                owner = __session__['name']

            self.dbapi.savePlancase(planid, caseid, scenario, ftags, name,
                owner, status, remark, plancaseid=plancaseid)

    def syncPlancase(self, planid):
        for plancase in self.dbapi.getPlancase(planid, fields='plancaseid,caseid,remark'):
            plancaseid, caseid, remark = plancase['plancaseid'], plancase['caseid'], plancase['remark']
            case = self.dbapi.getCtestcase(caseid=caseid)
            if len(case) == 0:
                self.dbapi.deletePlancase(plancaseid)
            else:
                scenario, name = case[0]['scenario'], case[0]['name']
                if Sql.isEmpty(remark):
                    remark = case[0]['remark']
                else:
                    remark = None
                self.dbapi.savePlancase(scenario=scenario, name=name, remark=remark, plancaseid=plancaseid)

    def savePlancaseRemark(self, plancaseid, caseid, scenario=None, name=None, remark=None, __session__=None):
        if Sql.isEmpty(plancaseid) or Sql.isEmpty(caseid):return
        owner = __session__['name']
        self.dbapi.saveCtestcase(scenario=scenario, name=name, remark=remark, caseid=caseid)
        self.dbapi.savePlancase(scenario=scenario, name=name, remark=remark, owner=owner, plancaseid=plancaseid)

    def getPlancase(self, planid=None, status=None, owner=None, scenarioName=None, caseName=None):
        return self.dbapi.getPlancase(planid, None, owner, status, scenarioName, caseName)

    def deletePlancase(self, plancaseid):
        return self.dbapi.deletePlancase(plancaseid)

    def setPlancase(self, plancaseid, status, __session__):
        return self.dbapi.setPlancase(plancaseid, status, __session__['name'])

    def resetPlancaseresult(self, planid, __session__):
        if Sql.isEmpty(planid):return 0
        return self.dbapi.setPlancase(None, 0, __session__['name'], planid, curstatus=1)

    def savePlandaily(self, planid, day, status, progress, caseprogress, costtime, costman,
            starttime, endtime, summary, issues, dailyId=None):
        if dailyId is None:
            daily = self.dbapi.getPlandaily(planid, day)
            if len(daily) > 0:
                dailyId = daily[0]['dailyId']
        caseprogress = self.calcPlancaseprogress(planid)
        self.dbapi.saveCtestplanStatus(planid, status, progress, starttime, endtime)
        return self.dbapi.savePlandaily(planid, day, status, progress, caseprogress, costtime, costman, summary, issues, dailyId)

    def getPlandaily(self, planid=None, day=None, dailyId=None):
        return self.dbapi.getPlandaily(planid, day, dailyId)

    def _summaryPlancases(self, planid):
        paased, failed, total = self.dbapi.countPlancase(planid, 1)[0]['count'], self.dbapi.countPlancase(planid, 2)[0]['count'], self.dbapi.countPlancase(planid)[0]['count']
        percent = 0 if total <= 0 else (paased + failed) * 100 / total
        return {'paased':paased, 'failed':failed, 'total':total, 'percent':percent}

    def calcPlancaseprogress(self, planid):
        plancase = self._summaryPlancases(planid)
        return "" if plancase['total'] == 0 else "{percent}% ({paased} + {failed}/{total})".format(**plancase)

    planStatusFinished = 3
    def getPlanSummary(self, planid):
        psummary = self.dbapi.getPlandaily(planid, limit=1)
        if len(psummary) == 1 and psummary[0]['status'] == self.planStatusFinished:
            return psummary[0]

    def getPlanSummaryReport(self, planid, summary, issues, isSetFinish=False):
        isSetFinish = str(isSetFinish).lower() == 'true'
        psummary = self.getPlanSummary(planid)
        if psummary is None:
            day = self.getDay()
        else:
            day = psummary['day']
        if isSetFinish:
            self.savePlandaily(planid, day, status=self.planStatusFinished,
                progress=100, caseprogress=None, costtime=None, costman=None,
                starttime=None, endtime=None, summary=summary, issues=issues)

        cplan = self.getCtestplanById(planid)[0]
        casereport = self.getCtestplancasereport(planid)
        subject = cprop.getVal("plan", "reportSubject").format(**cplan)
        emailbody = self.emailRp.formatPlanreport(cplan['reportTarget'], cplan['reportSummary'],
                summary, issues, casereport)
        return subject, emailbody

    def sendPlanSummaryEmail(self, planid, summary, issues, sender, receiver, ccReceiver, isSetFinish):
        subject, emailbody = self.getPlanSummaryReport(planid, summary, issues, isSetFinish)

        open("testreport.html", "wb").write(emailbody)
        smtpSender = cprop.getVal("email", "smtpSender")
        smtpAddr = cprop.getVal("email", "smtpAddr")
        smtpLogin = cprop.getVal("email", "smtpLogin")
        mimeMail = self.emailRp.makeEmail(sender, receiver, ccReceiver, subject, emailbody)
        self.dbapi.saveCtestplanStatus(planid, mailto=receiver, mailfrom=sender, mailcc=ccReceiver)
        return self.emailRp.sendEmail(smtpAddr, smtpLogin, smtpSender, receiver, ccReceiver, mimeMail)

    def getDay(self):
        return time.strftime('%Y-%m-%d')

    def getPlandailyEmail(self, planid, day=None):
        plan = self.dbapi.getCtestplan(planid=planid)[0]
        subject, title = self.emailRp.formatSubject(plan, day)
        
        dailys = []
        for daily in self.dbapi.getPlandaily(planid):
            dailys.append(self.emailRp.formatDaily(daily))
        return subject, self.emailRp.formatPlans(dailys, title)

    def sendPlandailyEmail(self, planid, day, sender, receiver, ccReceiver=''):
        subject, htmlBody = self.getPlandailyEmail(planid, day)

        smtpSender = cprop.getVal("email", "smtpSender")
        smtpAddr = cprop.getVal("email", "smtpAddr")
        smtpLogin = cprop.getVal("email", "smtpLogin")
        mimeMail = self.emailRp.makeEmail(sender, receiver, ccReceiver, subject, htmlBody)
        self.dbapi.saveCtestplanStatus(planid, mailto=receiver, mailfrom=sender, mailcc=ccReceiver)
        return self.emailRp.sendEmail(smtpAddr, smtpLogin, smtpSender, receiver, ccReceiver, mimeMail)

    def getPlanReport(self, ptype, inStatus=None, outStatus=None,
            fnid=None, nid1=None, nid2=None, name='all', tags=None, starttime1=None, starttime2=None):

        names = name.split(',')
        planList = []
        for n in names:
            if n.strip() == "":
                continue
            
            plans = self.dbapi.getCtestplan(fnid, nid1, nid2, ptype=ptype, inStatus=inStatus, outStatus=outStatus,
                starttime1=starttime1, starttime2=starttime2, name=(None if n == 'all' else n), tags=tags)
            if n != 'all':
                self.emailRp.addPlangroupTitle(n, planList)
            for plan in plans:
                planid = plan['planid']
                daily = self.dbapi.getPlandaily(planid, limit=1)
                self.emailRp.addPlangroup(plan, daily, planList)
        return self.emailRp.formPlangroup(planList)

    def sendPlanReport(self, sender, receiver, ccReceiver, subject,
            ptype, inStatus=None, outStatus=None,
            fnid=None, nid1=None, nid2=None, name='all', tags=None, starttime1=None, starttime2=None):
        htmlBody = self.getPlanReport(ptype, inStatus, outStatus, fnid, nid1, nid2, name, tags, starttime1, starttime2)

        smtpSender = cprop.getVal("email", "smtpSender")
        smtpAddr = cprop.getVal("email", "smtpAddr")
        smtpLogin = cprop.getVal("email", "smtpLogin")
        mimeMail = self.emailRp.makeEmail(sender, receiver, ccReceiver, subject, htmlBody)
        return self.emailRp.sendEmail(smtpAddr, smtpLogin, smtpSender, receiver, ccReceiver, mimeMail)

    def getTestEnv(self, envname=None, hostip=None, vmaccount=None, owner=None, ownerStatus=None, fnid=None, nid1=None, nid2=None, testenvid=None):
        return self.dbapi.getTestEnv(envname, hostip, vmaccount, owner, ownerStatus, fnid, nid1, nid2, testenvid)

    def deleteTestEnv(self, testenvid):
        return self.dbapi.deleteTestEnv(testenvid)

    def saveTestEnv(self, envname, tags=None, hostip=None, hostaccount=None, hostinfo=None,
            vmaccount=None, vmammounts=None, vminfo=None, owner=None, ownerStatus=None, ownerInfo=None, ownerStartTime=None, ownerEndTime=None,
            fnid=None, nid1=None, nid2=None, testenvid=None):
        return self.dbapi.saveTestEnv(envname, tags, hostip, hostaccount, hostinfo, vmaccount, vmammounts, vminfo, owner, ownerStatus, ownerInfo, ownerStartTime, ownerEndTime, fnid, nid1, nid2, testenvid)

# test config
    def getTestConfig(self, subject=None, stype=None, cname=None, ckey=None, fnid=None, nid1=None, nid2=None, configid=None):
        return {'fileLink':cprop.getVal('cconfig', 'fileLink'), 'data':self.dbapi.getTestConfig(subject, stype, cname, ckey, fnid, nid1, nid2, configid)}

    def getPlanTemplate(self, cname):
        return self.dbapi.getTestConfig("plan", ckey="template", cname=cname, status=1, fields="ccontent")

    def saveTestConfig(self, cname, calias=None, status=None, subject=None, ckey=None, stype=None, ccontent=None,
            fnid=None, nid1=None, nid2=None, configid=None, __session__=None):
        owner = __session__['name']

        if stype == '3' and ccontent.strip() != '':
            fileFolder = cprop.getVal('cconfig', 'fileFolder')
            with open(fileFolder + cname, 'wb') as f:
                f.write(ccontent)
        return self.dbapi.saveTestConfig(cname, calias, status, subject, ckey, stype, ccontent, owner, fnid, nid1, nid2, configid)

    def deleteTestConfig(self, configid):
        return self.dbapi.deleteTestConfig(configid)

    # deploy
    def _isRelativeDeploy(self, owner, deploy):
        return (deploy['owner'] == owner or deploy['creator'] == owner)

    def addDeploy(self, version, procode, branch, pendtime=None, owner=None, notifyer=None, remark=None,
            fnid=None, nid1=None, nid2=None, phaseInit=False, deployid=None, __session__=None):
        proname, protype, brancharg, deployarg = None, None, None, None
        phase, status = (1 if phaseInit else 0, 0) if deployid is None else (None, None)
        creator = __session__['name']
        if deployid is not None:
            deploy = self.dbapi.getCdeploy(deployid=deployid)[0]
            if not __session__['admin'] and not self._isRelativeDeploy(creator, deploy):
                raise Exception("Not the creator or owner")
        return self.dbapi.saveCdeploy(version, procode, proname, protype, branch, brancharg, pendtime,
            creator, owner, notifyer, remark, fnid, nid1, nid2, phase, status, deployarg, deployid=deployid)

    def getDeploy(self, project=None, version=None, branch=None, phase=None,
            fnid=None, nid1=None, nid2=None, isRelativeOwner="false", __session__=None):
        creator = __session__['name'] if str(isRelativeOwner).lower() == "true" else None
        return self.dbapi.getCdeploy(project, version, branch, phase, creator, fnid, nid1, nid2)

    def deleteDeploy(self, deployid, __session__=None):
        creator = None if __session__['admin'] else  __session__['name'] 
        if self.dbapi.deleteCdeploy(deployid, creator) == 0:
            raise Exception("Not the creator, delete failed")

    def getProject(self, condition=None):
        pros = self.dbapi.getTestConfig("deploy", ckey="project", status=1, fields="cname,calias as info")
        return pros

    def getVersion(self, condition=None):
        pros = self.dbapi.getTestConfig("plan", ckey="version", status=1, fields="cname,ccontent as info")
        return pros

    def getBranch(self, project):
        pass

    def getDeployargs(self, project=None, phase=None):
        pros = self.dbapi.getTestConfig("deploy", ckey="deployargs", status=1)
        return pros
    
    def startDeploy(self, deployid, deployargs, __session__):
        if Sql.isEmpty(deployid):raise Exception("Not found deployid")
        deploy = self.dbapi.getCdeploy(deployid=deployid)[0]
        owner = __session__['name']
        if self._isRelativeDeploy(owner, deploy):
            if deploy['status'] == '1': return deploy['status']
            self.dbapi.saveCdeploy(status=1, deployarg=deployargs, deploytimes=deploy['deploytimes'] + 1, isSetModifytime=True, deployid=deployid)
            return "1"
        else:
            raise Exception("Not the creator or owner")

    def getDeployStatus(self, deployid):
        if Sql.isEmpty(deployid):raise Exception("Not found deployid")
        deploy = self.dbapi.getCdeploy(deployid=deployid)[0]
        # checking deploy status
        if deploy['status'] == '1':  self.dbapi.saveCdeploy(status=2, deployid=deployid)
        return "2"

    def changeDeployflow(self, deployid, nextInt, chowner=None, __session__=None):
        owner = __session__['name']
        deploy = self.dbapi.getCdeploy(deployid=deployid, creator=owner)
        if len(deploy) == 1:
            deploy = deploy[0]
            if owner != deploy['owner']:
                return 2, "Owner not match"
            else: phase = int(deploy['phase']) + int(nextInt)
            return self.dbapi.saveCdeploy(phase=phase, owner=chowner, deployid=deployid), "Changed"
        else:
            return 3, "Not authorized"

@cloudModule(handleUrl='/', imports="CTestPlanAPi.dbapi")
class AuthApi(LocalMemSessionHandler):
    def __init__(self):
        self.dbapi = object()  # imported from CTestPlanAPi
        self.sysadmin = cprop.getVal("plan", "sysadmin")
        self.tjson = TimmerJson()
        LocalMemSessionHandler.__init__(self)

    def __setup__(self):
        self.redirectPath = '/clogin.html'
        self.__ignoreMethods__('checkLogin', 'registerOwner')
        self.__ignorePaths__('/clogin.html', '/cservice/CServiceTool/registServer', '/cservice/CTestPlanAPi/exportCtestcase', '/uploads/mserver.tar')

    def getOwners(self):
        pros = self.dbapi.getTestConfig("plan", ckey="owner", status=1, fields="cname as info,calias")
        return pros

    def registerOwner(self, cname, calias, email=None, passwd=None):
        owners = self.dbapi.getTestConfig(subject="plan", ckey="owner", cname=cname)
        if len(owners) > 0:
            raise Exception("Already exist")
        status, subject, ckey, stype, ccontent, owner = 1, "plan", "owner", 1, {"email":email}, "register"
        fnid, nid1, nid2 = 66, 8, None
        self.dbapi.saveTestConfig(cname, calias, status, subject, ckey, stype, ccontent, owner, fnid, nid1, nid2)
        raise RedirectException("/clogin.html?register=success")

    def checkLogin(self, name, passwd, loginfrom="", __session__=None):
        owners = self.dbapi.getTestConfig(subject="plan", ckey="owner", cname=name)
        owner = owners[0] if len(owners) >= 1 else None
        if owner is not None and (owner['cname'] == name or owner['calias'] == name) and owner['status'] == 1 :
            __session__['name'] = owner['calias']
            __session__['admin'] = self.sysadmin.__contains__(owner['cname'])
            __session__['authorized'] = True
            url = loginfrom[6:]
            if not url.__contains__(".html") and not url.__contains__("?"):
                url = '/'
        else:
            url = "/clogin.html?login=Failed"
        raise RedirectException(url)

    def getLoginInfo(self, __session__):
        return {'name':__session__['name']}

    def logout(self, session):
        return self.__invalidateSession__(session['id'])
    
    def getMailList(self):
        emails = self.tjson.getKey("email")
        if emails is None:
            pros = self.dbapi.getTestConfig("plan", ckey="owner", status=1, fields="ccontent")
            emails = []
            for p in pros:
                try:
                    addr = eval(p['ccontent'])['email']
                    if addr is not None and addr != "": emails.append({'addr':addr})
                except:pass
            emails = tuple(emails)
            self.tjson.addKey("email", emails)

        return emails + self.dbapi.getTestConfig("plan", ckey="email", status=1, fields="cname as addr")

    def __checkSessionAuthStatus__(self, session, reqObj, reqPath, reqParam):
        return session.__contains__('authorized')

if __name__ == "__main__":
    from cserver import servering
    cprop.load("cplan.ini")
    servering("-p 8089 -f webs  -m cplan.html  -t testoolplatform.py -t testtoolcenter.py")
