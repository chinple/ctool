# -*- coding: utf8 -*-
'''
Created on 2016-10-2

@author: chinple
'''
from db.sqllib import SqlConnFactory, Sql
from db.mysqldb import MysqldbConn
from cserver import cprop, cloudModule
from libs.timmer import TimmerOperation
import time
from libs.syslog import slog
from libs.objop import ObjOperation
import base64
from server.csession import LocalMemSessionHandler
from server.chandle import RedirectException, ReturnFileException
from libs.parser import toJsonObj
from server.cclient import curl

class CtestDbOp:
    def __init__(self):
        sqlConfig = {'host':cprop.getVal("db", "host"), 'port':cprop.getInt("db", "port"),
            'user':cprop.getVal("db", "user"), 'passwd':cprop.getVal("db", "passwd"),
            'db':cprop.getVal("db", "db"), 'charset':'utf8'}
        self.sqlConn = SqlConnFactory(MysqldbConn, sqlConfig)

    def saveCtree(self, name, fnid=-1, nid=None):
        sql = self.sqlConn.getSql("ctree", Sql.insert if nid is None else Sql.update, True)
        sql.appendValueByJson({'name':name, "fnid":fnid, "nid":nid})
        sql.appendWhere("nid", nid)
        return sql.execute()

    def getCtree(self, fnid=None, name=None, nid=None):
        sql = self.sqlConn.getSql("ctree", Sql.select, True)
        sql.appendWhereByJson({'name':name, "fnid":fnid, "nid":nid})
        return sql.execute()
    def deleteCtree(self, nid):
        if Sql.isEmpty(nid):
            return 0
        sql = self.sqlConn.getSql("ctree", Sql.delete, True)
        sql.appendWhere("nid", nid)
        return sql.execute()
# test case
    def saveCtestcase(self, scenario=None, tags=None, name=None, ttype=None, priority=None, steps=None, remark=None, owner=None,
            fnid=None, nid1=None, nid2=None, caseid=None):
        modifytime = TimmerOperation.getFormatTime(time.time())
        sql = self.sqlConn.getSql("testcase", Sql.insert if Sql.isEmpty(caseid) else Sql.update, True)
        sql.appendValueByJson({'scenario':scenario, 'tags':tags, 'name':name, "ttype":ttype, "priority":priority,
            'steps':steps, "remark":remark, "owner":owner, 'modifytime':modifytime,
            "fnid":fnid, "nid1":nid1, "nid2":nid2, "caseid":caseid})
        sql.appendWhere("caseid", caseid)
        return sql.execute()

    def getCtestcase(self, fnid=None, nid1=None, nid2=None,
            searchKey=None, ttype=None, priority=None, name=None, owner=None, caseid=None):
        sql = self.sqlConn.getSql("testcase", Sql.select, True)
        conditions = []
        if not Sql.isEmpty(fnid):
            conditions.append('fnid = %s' % fnid)
        if not Sql.isEmpty(nid1):
            conditions.append('nid1 = %s' % nid1)
        if not Sql.isEmpty(nid2):
            conditions.append('nid2 = %s' % nid2)
        if len(conditions) > 0:
            sql.appendCondition("(%s)" % (" or ".join(conditions)))

        sql.appendWhereByJson({'name':name, "ttype":ttype, "priority":priority,
            "owner":owner, "caseid":caseid})
        if not Sql.isEmpty(searchKey):
            searchKey = '%%%s%%' % searchKey
            sql.appendCondition("(name like '%s' or tags like '%s'or scenario like '%s')" % (searchKey, searchKey, searchKey))
        sql.orderBy("scenario,name")
        return sql.execute()

    def deleteCtestcase(self, caseid):
        if Sql.isEmpty(caseid):
            return 0
        sql = self.sqlConn.getSql("testcase", Sql.delete, True)
        sql.appendWhere("caseid", caseid)
        return sql.execute()

    def _checkDate(self, d):
        return None if Sql.isEmpty(d) else d
# test plan
    def saveCtestplan(self, name=None, owner=None, tags=None, summary=None, issues=None,
            ptype=None, priority=None, status=None, progress=None,
            pstarttime=None, pendtime=None, starttime=None, endtime=None,
            mailto=None, fnid=None, nid1=None, nid2=None, planid=None):
        # status: created, executing, finished, paused
        pstarttime = self._checkDate(pstarttime)
        pendtime = self._checkDate(pendtime)
        starttime = self._checkDate(starttime)
        endtime = self._checkDate(endtime)

        sql = self.sqlConn.getSql("testplan", Sql.insert if Sql.isEmpty(planid) else Sql.update, True)
        sql.appendValueByJson({'name':name, 'owner':owner, 'tags':tags, 'summary':summary, 'issues':issues,
            'ptype':ptype, 'priority':priority, "status":status, "progress":progress,
            'pstarttime':pstarttime, "pendtime":pendtime, "starttime":starttime, 'endtime':endtime,
            "mailto":mailto, "fnid":fnid, "nid1":nid1, "nid2":nid2, "planid":planid})
        sql.appendWhere("planid", planid)
        return sql.execute()

    def saveCtestplanStatus(self, planid, status=None, progress=None, starttime=None, endtime=None,
            mailto=None, mailfrom=None, mailcc=None):
        if Sql.isEmpty(planid):
            return 0
        sql = self.sqlConn.getSql("testplan", Sql.update, True)
        sql.appendValueByJson({ 'status':status, 'progress':progress, 'starttime':starttime, 'endtime':endtime,
            'mailto':mailto, 'mailfrom':mailfrom, 'mailcc':mailcc})
        sql.appendWhere("planid", planid)
        return sql.execute()

    def getCtestplan(self, fnid=None, nid1=None, nid2=None,
            nameOrTags=None, ptype=None, priority=None, inStatus=None, outStatus=None,
            starttime1=None, starttime2=None, owner=None, name=None, tags=None, planid=None):
        sql = self.sqlConn.getSql("testplan", Sql.select, True)

        conditions = []
        if not Sql.isEmpty(fnid):
            conditions.append('fnid = %s' % fnid)
        if not Sql.isEmpty(nid1):
            conditions.append('nid1 = %s' % nid1)
        if not Sql.isEmpty(nid2):
            conditions.append('nid2 = %s' % nid2)
        if len(conditions) > 0:
            sql.appendCondition("(%s)" % (" or ".join(conditions)))

        if not Sql.isEmpty(nameOrTags):
            nameOrTags = '%%%s%%' % nameOrTags
            sql.appendCondition("(name like '%s' or tags like '%s' or owner like '%s')" % (nameOrTags, nameOrTags, nameOrTags))
        if not Sql.isEmpty(name):
            name = '%%%s%%' % name
            sql.appendWhere('name', name, 'like')
        if not Sql.isEmpty(tags):
            tags = '%%%s%%' % tags
            sql.appendWhere('tags', tags, 'like')
        
        sql.appendWhereByJson({"owner":owner, 'priority':priority, 'status':inStatus, "planid":planid})
        sql.appendWhere('ptype', ptype, 'in')
        sql.appendWhere('status', outStatus, '!=')
        sql.appendWhere("starttime", starttime1, ">=").appendWhere("starttime", starttime2, "<")

        sql.orderBy("status,pendtime,ptype,fnid desc,tags,name")
        return sql.execute()

    def deleteCtestplan(self, planid):
        if Sql.isEmpty(planid):
            return 0
        sql = self.sqlConn.getSql("testplan", Sql.delete, True)
        sql.appendWhere("planid", planid)
        return sql.execute()

# plan related
    def savePlancase(self, planid=None, caseid=None, scenario=None, tags=None, name=None, owner=None, status=None, remark=None, plancaseid=None):
        # status: not-start, executing, passed, failed
        modifytime = TimmerOperation.getFormatTime(time.time())
        sql = self.sqlConn.getSql("plancase", Sql.insert if Sql.isEmpty(plancaseid) else Sql.update, True)
        sql.appendValueByJson({'planid':planid, "caseid":caseid, "tags":tags, "scenario":scenario, "name":name,
            'owner':owner, 'remark':remark, "status":status, "modifytime":modifytime})
        sql.appendWhere("plancaseid", plancaseid)
        return sql.execute()

    def setPlancase(self, plancaseid, status, owner):
        # status: not-start, executing, passed, failed
        sql = self.sqlConn.getSql("plancase", Sql.update, True)
        sql.appendValueByJson({"status":status, 'owner':owner})
        sql.appendWhere("plancaseid", plancaseid)
        return sql.execute()

    def getPlancase(self, planid, caseid=None, owner=None, status=None, caseTags=None, caseName=None, fields='*'):
        sql = self.sqlConn.getSql("plancase", Sql.select, True, fields)
        sql.appendWhereByJson({'planid':planid, "caseid":caseid,
            "status":status })

        if not Sql.isEmpty(owner):
            owner = '%%%s%%' % owner
            sql.appendCondition("(owner like '%s')" % (owner))

        if not Sql.isEmpty(caseTags):
            caseTags = '%%%s%%' % caseTags
            sql.appendCondition("(tags like '%s' or scenario like '%s')" % (caseTags, caseTags))

        if not Sql.isEmpty(caseName):
            caseName = '%%%s%%' % caseName
            sql.appendCondition("(name like '%s')" % (caseName))

        sql.orderBy('tags,scenario,caseid')
        return sql.execute()

    def countPlancase(self, planid=None, status=None):
        sql = self.sqlConn.getSql("plancase", Sql.select, True, 'count(*) as count')
        sql.appendWhereByJson({'planid':planid, "status":status })
        return sql.execute()

    def deletePlancase(self, plancaseid):
        if Sql.isEmpty(plancaseid):
            return 0
        sql = self.sqlConn.getSql("plancase", Sql.delete, True)
        sql.appendWhere("plancaseid", plancaseid)
        return sql.execute()

    def savePlandaily(self, planid, day, status, progress, caseprogress,
            costtime, costman, summary, issues, dailyId=None):
        sql = self.sqlConn.getSql("plandaily", Sql.insert if Sql.isEmpty(dailyId) else Sql.update, True)
        sql.appendValueByJson({'planid':planid, "day":day, "status":status, "progress":progress, 'caseprogress':caseprogress,
            'costtime':costtime, 'costman':costman, 'summary':summary, 'issues':issues, "dailyId":dailyId})
        sql.appendWhere("dailyId", dailyId)
        return sql.execute()

    def getPlandaily(self, planid=None, day=None, dailyId=None, limit=None, status=None):
        sql = self.sqlConn.getSql("plandaily", Sql.select, True)
        sql.appendWhereByJson({'planid':planid, "dailyId":dailyId, 'day':day, "status":status})
        sql.limit = limit
        sql.orderBy("day DESC")
        return sql.execute()
    
# test env
    def getTestEnv(self, envname, hostip, vmaccount, owner, ownerStatus, fnid, nid1, nid2, testenvid=None):
        sql = self.sqlConn.getSql("testenv", Sql.select, True)
        sql.appendWhereByJson({'hostip': hostip,
            'owner':owner, 'ownerStatus': ownerStatus})

        conditions = []
        if not Sql.isEmpty(fnid):
            conditions.append('fnid = %s' % fnid)
        if not Sql.isEmpty(nid1):
            conditions.append('nid1 = %s' % nid1)
        if not Sql.isEmpty(nid2):
            conditions.append('nid2 = %s' % nid2)
        if len(conditions) > 0:
            sql.appendCondition("(%s)" % (" or ".join(conditions)))

        if not Sql.isEmpty(vmaccount):
            vmaccount = '%%%s%%' % vmaccount
            sql.appendCondition("(vmaccount like '%s')" % (vmaccount))

        if not Sql.isEmpty(envname):
            envname = '%%%s%%' % envname
            sql.appendCondition("(envname like '%s' or tags like '%s')" % (envname, envname))
        # 'vmammounts': vmammounts
        # 'ownerStartTime': ownerStartTime, 'ownerEndTime': ownerEndTime,
        sql.appendWhere("testenvid", testenvid)
        return sql.execute()

    def saveTestEnv(self, envname, tags, hostip, hostaccount, hostinfo,
            vmaccount, vmammounts, vminfo, owner, ownerStatus, ownerInfo, ownerStartTime, ownerEndTime,
            fnid, nid1, nid2, testenvid=None):

        sql = self.sqlConn.getSql("testenv", Sql.insert if Sql.isEmpty(testenvid) else Sql.update, True)
        sql.appendValueByJson({'envname':envname, 'tags':tags, 'hostip': hostip, 'hostaccount': hostaccount, 'hostinfo': hostinfo,
            'vmaccount': vmaccount, 'vmammounts': vmammounts, 'vminfo':vminfo,
            'owner':owner, 'ownerStatus': ownerStatus, 'ownerInfo': ownerInfo, 'ownerStartTime': ownerStartTime, 'ownerEndTime': ownerEndTime,
            'fnid': fnid, 'nid1': nid1, 'nid2': nid2})
        sql.appendWhere("testenvid", testenvid)
        return sql.execute()

    def deleteTestEnv(self, testenvid):
        if Sql.isEmpty(testenvid):
            return 0
        sql = self.sqlConn.getSql("testenv", Sql.delete, True)
        sql.appendWhere("testenvid", testenvid)
        return sql.execute()

# test config
    def getTestConfig(self, subject=None, stype=None, cname=None, ckey=None, fnid=None, nid1=None, nid2=None, configid=None):
        sql = self.sqlConn.getSql("cconfig", Sql.select, True)
        sql.appendWhereByJson({'configid': configid, 'stype':stype})

        conditions = []
        if not Sql.isEmpty(fnid):
            conditions.append('fnid = %s' % fnid)
        if not Sql.isEmpty(nid1):
            conditions.append('nid1 = %s' % nid1)
        if not Sql.isEmpty(nid2):
            conditions.append('nid2 = %s' % nid2)
        if len(conditions) > 0:
            sql.appendCondition("(%s)" % (" or ".join(conditions)))

        if not Sql.isEmpty(subject):
            subject = '%%%s%%' % subject
            sql.appendCondition("(subject like '%s')" % (subject))

        if not Sql.isEmpty(cname):
            cname = '%%%s%%' % cname
            sql.appendCondition("(cname like '%s')" % (cname))
        
        if not Sql.isEmpty(ckey):
            ckey = '%%%s%%' % ckey
            sql.appendCondition("(ckey like '%s')" % (ckey))

        return sql.execute()

    def saveTestConfig(self, cname, subject, ckey, stype, ccontent, owner, fnid, nid1, nid2, configid=None):
        modifytime = TimmerOperation.getFormatTime(time.time())

        sql = self.sqlConn.getSql("cconfig", Sql.insert if Sql.isEmpty(configid) else Sql.update, True)
        sql.appendValueByJson({'cname':cname, 'subject':subject, 'ckey': ckey, 'stype': stype, 'ccontent': ccontent,
            "owner":owner, 'modifytime':modifytime, 'fnid': fnid, 'nid1': nid1, 'nid2': nid2})
        sql.appendWhere("configid", configid)
        return sql.execute()

    def deleteTestConfig(self, configid):
        if Sql.isEmpty(configid):
            return 0
        sql = self.sqlConn.getSql("cconfig", Sql.delete, True)
        sql.appendWhere("configid", configid)
        return sql.execute()

class EmailReportor:
    def __init__(self):
        self.emailDailySubject = cprop.getVal('plan', 'emailDailySubject')
        self.emailDailySp = cprop.getVal('plan', 'emailDailySp')
        self.emailDailyRow = cprop.getVal('plan', 'emailDailyRow')
        self.emailDailyBody = cprop.getVal('plan', 'emailDailyBody')
        self.planLink = cprop.getVal('plan', 'planLink')
        self.emailDailyTitle = cprop.getVal('plan', 'emailDailyTitle')

        self.riskStatusDefine = cprop.getVal('plan', 'planStatus').split()
        self.emailPlanBodyTemplate = cprop.getVal('plan', 'emailPlanBodyTemplate')
        emailPlanRowFormat = 'textarea'
        self.emailPlanRowFormat = ObjOperation.tryGetVal({'textarea':"<textarea>%s</textarea>", 'pre':"<pre>%s</pre>"}, emailPlanRowFormat, '%s')
        self.emailPlanRow = cprop.getVal('plan', 'emailPlanRow')
        self.emailPlanRowTitle = cprop.getVal('plan', 'emailPlanRowTitle')
        
        self.reportBodyTemplate = cprop.getVal('plan', 'reportBodyTemplate')

# plan report
    def formatPlanreport(self, planReportTarget, planReportDetail, planreportSummary, planreportIssues, planReportCaseSummary):
        planreport = open(self.reportBodyTemplate).read()
        planreport = planreport.replace('{planReportTarget}', planReportTarget)
        planreport = planreport.replace('{planReportDetail}', planReportDetail)
        planreport = planreport.replace('{planreportSummary}', planreportSummary)
        planreport = planreport.replace('{planreportIssues}', planreportIssues)
        planreport = planreport.replace('{planReportCaseSummary}', planReportCaseSummary)
        return planreport

# plan group
    def formatSubject(self, plan, day):
        plan['day'] = day
        plan['planLink'] = self.planLink
        subject = self.emailDailySubject.format(**plan)
        title = self.emailDailyTitle.format(**plan)
        return subject, title

    def formatDaily(self, daily):
        day, progress, caseprogress = daily['day'], daily['progress'], daily['caseprogress']
        summary, issues = daily['summary'], daily['issues']
        daily['day'] = day.strftime("%Y-%m-%d")
        daily['progress'] = '%s%%' % progress
        daily['caseprogress'] = 'N/A' if caseprogress is None else ('%s%%' % caseprogress)
        space = '    '
        daily['summary'] = space + ('' if summary is None else summary.replace('\n', '\n' + space))
        daily['issues'] = space + ('' if issues is None else issues.replace('\n', '\n' + space))
        return self.emailDailyRow.format(**daily)
    
    def formatPlans(self, dailys, title):
        return self.emailDailyBody.format(plan=("\n" + self.emailDailySp).join(dailys), sp=self.emailDailySp, title=title)

    def addPlangroupTitle(self, name, plans):
        plans.append(self.emailPlanRowTitle.format(name=name))
    def addPlangroup(self, plan, daily, plans):
        plan['status'] = self.riskStatusDefine[plan['status']]
        plan['planLink'] = self.planLink
        plan['summary'] = self.emailPlanRowFormat % plan['summary']
        plan['pstarttime'] = str(plan['pstarttime']).split(' ')[0]
        plan['pendtime'] = str(plan['pendtime']).split(' ')[0]
        plan['endtime'] = str(plan['endtime']).split(' ')[0]
        plan['starttime'] = str(plan['starttime']).split(' ')[0]

        daily = daily[0] if len(daily) > 0 else None

        plan['progress'] = '' if daily is None else ('%s%%' % daily['progress'])
        plan['dailyDay'] = '' if daily is None else str(daily['day']).split(' ')[0]
        plan['dailySummary'] = '' if daily is None else (self.emailPlanRowFormat % daily['summary'])
        plan['dailyIssues'] = '' if daily is None else (self.emailPlanRowFormat % daily['issues'])
        plans.append(self.emailPlanRow.format(**plan))

    def formPlangroup(self, plans):
        return open(self.emailPlanBodyTemplate).read().replace("{plans}", "".join(plans))

    def makeEmail(self, sender, receiver, ccReceiver, subject, htmlBody):
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        mimeMail = MIMEMultipart()
        mimeMail.add_header("Date", time.strftime("%A, %d %B %Y %H:%M"))
        mimeMail.add_header("From", sender)
        mimeMail.add_header("To", receiver)
        mimeMail.add_header("cc", ccReceiver)
        mimeMail.add_header("Subject", subject)
        mimeMail.attach(MIMEText(_text=htmlBody.encode("utf8"), _subtype="html", _charset="utf8"))
        return mimeMail

    def sendEmail(self, smtpAddr, smtpLogin, smtpSender, receiver, ccReceiver, mimeMail):
        try:
            if receiver == "":
                raise Exception("No receiver")
            receiver = (receiver + ";" + ccReceiver).replace(';;', ';').split(";")
            smtpAccount, smtpPasswd = base64.decodestring(smtpLogin).split("/")
            from smtplib import SMTP
            slog.info("Sending mail(SMTP %s):\n\t%s -> %s" % (smtpAddr, smtpAccount, receiver))
            smtp = smtpAddr.split(':')
            smtpServer = smtp[0]
            smtpPort = int(ObjOperation.tryGetVal(smtp, 1, 25))
            smtpClient = SMTP(smtpServer, smtpPort)
            try:
                smtpClient.ehlo()
                smtpClient.login(smtpAccount, smtpPasswd)
            except:pass
            smtpClient.sendmail(smtpSender, receiver, mimeMail.as_string())
            smtpClient.quit()
            return 'Success'
        except Exception as ex:
            slog.info("Fail to send mail for: %s" % ex)
            return str(ex)

    # test cases
    def formatTestCase(self, testcases):
        cases = []
        for t in testcases:
            cases.append(cprop.getVal("testcase", 'caseRow').format(**t))
        return open(cprop.getVal("testcase", 'caseReportTemplate')).read().replace("{testcases}", "".join(cases))

@cloudModule()
class CTestPlanAPi:
    def __init__(self):
        self.dbapi = CtestDbOp()
        self.emailRp = EmailReportor()
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
    def getCtestcase(self, fnid=None, nid1=None, nid2=None,
            searchKey=None, ttype=None, priority=None, name=None, owner=None, caseid=None):
        return self.dbapi.getCtestcase(fnid, nid1, nid2, searchKey, ttype, priority, name, owner, caseid)

    def exportCtestcase(self, fnid=None, nid1=None, nid2=None, searchKey=None, ttype=None, priority=None, owner=None):
        raise ReturnFileException(self.emailRp.formatTestCase(self.dbapi.getCtestcase(fnid, nid1, nid2, searchKey, ttype, priority, owner=owner)),
            'text/html')

    def deleteCtestcase(self, caseid):
        return self.dbapi.deleteCtestcase(caseid)

    def saveCtestplan(self, name=None, owner=None, tags=None, summary=None, issues=None,
            ptype=None, priority=None, status=None, progress=None,
            pstarttime=None, pendtime=None, starttime=None, endtime=None,
            mailto=None, fnid=None, nid1=None, nid2=None, planid=None):
        return self.dbapi.saveCtestplan(name, owner, tags, summary, issues, ptype, priority, status, progress, pstarttime, pendtime, starttime, endtime, mailto, fnid, nid1, nid2, planid)

    def updateCtestplan(self, planid, plan):
        if Sql.isEmpty(planid):return 0
        tryget = ObjOperation.tryGetVal
        return self.dbapi.saveCtestplan(owner=tryget(plan, 'owner', None), ptype=tryget(plan, 'ptype', None),
            priority=tryget(plan, 'priority', None), status=tryget(plan, 'status', None), progress=tryget(plan, 'progress', None),
            pendtime=tryget(plan, 'pendtime', None), endtime=tryget(plan, 'endtime', None), planid=planid)

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
            plan['pstarttime'] = str(plan['pstarttime']).split()[0]
            plan['pendtime'] = str(plan['pendtime']).split()[0]
            plan['starttime'] = str(plan['starttime']).split()[0]
            plan['endtime'] = str(plan['endtime']).split()[0]
            plan['reportTarget'] = cprop.getVal('plan', 'reportTarget').format(**plan)
            plan['reportSummary'] = cprop.getVal('plan', 'reportSummary').format(**plan)
            case = self.countPlancase(planid, 1)
            plan['reportSummary'] = plan['reportSummary'].format(**case)
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

    def getPlancase(self, planid=None, status=None, owner=None, caseTags=None, caseName=None):
        return self.dbapi.getPlancase(planid, None, owner, status, caseTags, caseName)

    def deletePlancase(self, plancaseid):
        return self.dbapi.deletePlancase(plancaseid)

    def setPlancase(self, plancaseid, status, __session__):
        return self.dbapi.setPlancase(plancaseid, status, __session__['name'])

    def savePlandaily(self, planid, day, status, progress, caseprogress, costtime, costman,
            starttime, endtime, summary, issues, dailyId=None):
        if dailyId is None:
            daily = self.dbapi.getPlandaily(planid, day)
            if len(daily) > 0:
                dailyId = daily[0]['dailyId']
        caseprogress = self.countPlancase(planid, 1)['percent']
        self.dbapi.saveCtestplanStatus(planid, status, progress, starttime, endtime)
        return self.dbapi.savePlandaily(planid, day, status, progress, caseprogress, costtime, costman, summary, issues, dailyId)

    def getPlandaily(self, planid=None, day=None, dailyId=None):
        return self.dbapi.getPlandaily(planid, day, dailyId)

    def countPlancase(self, planid=None, status=None):
        count, total = self.dbapi.countPlancase(planid, status)[0]['count'], self.dbapi.countPlancase(planid)[0]['count']
        percent = 0 if total <= 0 else count * 100 / total
        return {'count':count, 'total':total, 'percent':percent}

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

    def saveTestConfig(self, cname, subject, ckey, stype, ccontent, fnid=None, nid1=None, nid2=None, configid=None, __session__=None):
        owner = __session__['name']

        if stype == '3' and ccontent.strip() != '':
            fileFolder = cprop.getVal('cconfig', 'fileFolder')
            with open(fileFolder + cname, 'wb') as f:
                f.write(ccontent)
        return self.dbapi.saveTestConfig(cname, subject, ckey, stype, ccontent, owner, fnid, nid1, nid2, configid)

    def deleteTestConfig(self, configid):
        return self.dbapi.deleteTestConfig(configid)

class BugFreeApi:
    def __init__(self):
        sqlConfig = {'host':cprop.getVal("bugfree", "host"), 'port':cprop.getInt("bugfree", "port"),
            'user':cprop.getVal("bugfree", "user"), 'passwd':cprop.getVal("bugfree", "passwd"),
            'db':cprop.getVal("bugfree", "db"), 'charset':'utf8'}
        self.sqlConn = SqlConnFactory(MysqldbConn, sqlConfig)
        self.bfapi = cprop.getVal("bugfree", "bfapi")

    def getBfUser(self, username):
        sql = self.sqlConn.getSql("bf_test_user", Sql.select, True, 'username,realname,email')
        sql.appendWhereByJson({'username':username})
        return sql.execute()

    def _strmd5(self, s):
        import md5  
        m = md5.new()  
        m.update(s)  
        return m.hexdigest()
        
    def login(self, username, password):
        return {'status':True, 'name':username}

    def _bfLogin(self, username, password):
        resp = toJsonObj(curl("http://%s/api3.php?mode=getsid" % self.bfapi))
        sessionname = resp['sessionname']
        sessionid = resp['sessionid']
        rand = resp['rand']
        
        auth = self._strmd5(self._strmd5(username + self._strmd5(password)) + rand) 
        
        url = 'http://%s/api3.php?mode=login&&%s=%s&username=%s&auth=%s' % (self.bfapi, sessionname, sessionid, username, auth)
        login = toJsonObj(curl(url))

        user = self.getBfUser(username)
        return {'status':login['status'] == 'success', 'name':user[0]['realname'] if len(user) == 1 else 'NotExist'}

@cloudModule(handleUrl='/')
class AuthApi(LocalMemSessionHandler):
    def __init__(self):
        self.bugfree = BugFreeApi()
        LocalMemSessionHandler.__init__(self)
        self.redirectPath = '/clogin.html'
        self.__ignoreMethods__('checkLogin')
        self.__ignorePaths__('/clogin.html', '/cservice/AuthApi/checkLogin', '/cservice/CServiceTool/RegistServer')

    def checkLogin(self, name, password, loginfrom="", __session__=None):
        
        bglogin = self.bugfree.login(name, password)
        if bglogin['status']:
            __session__['name'] = bglogin['name']
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

    def __checkSessionAuthStatus__(self, session, reqObj, reqPath, reqParam):
        return session.__contains__('authorized')

if __name__ == "__main__":
    from cserver import servering
    cprop.load("cplan.ini")
    servering("-p 8089 -f webs  -m cplan.html  -t ctoolApi.py")
