# -*- coding: utf8 -*-
'''

@author: 
'''
from mtest import model, TestCaseBase, scenario
from testexecuting import CTestPlanAPi
from cserver import cprop
import os

@model()
class TestExecuting(TestCaseBase):
    @scenario(param={},
        where={})
    def testSummaryReport(self):
        cp = CTestPlanAPi()
        planid = 5
        summary = '''api 发布完成，验证通过
1. 提供api：recommend-cards，recommend-loans，主要做基本功能与压测
2. 前端由记账提供，未上线
3. 由于与外部团队配合，未配合记账方计划延迟2天发布
4. 了解了下测试流程及测试环境、预发与线上环境

赞：本次发布采用约定分支命名发布，发布比较顺利：test_20170622'''
        issues = '''1. 由于请求ip位置访问taobao被限，同一个ip第二次访问的请求可能在3s后返回；目前在压测location-service未替代方案
    

2. 测试对各业务模块未有较全的业务文档和用例，版本后需要增加相关文档    
1. 由于请求ip位置访问taobao被限，同一个ip第二次访问的请求可能在3s后返回；目前在压测location-service未替代方案
    

2. 测试对各业务模块未有较全的业务文档和用例，版本后需要增加相关文档    
1. 由于请求ip位置访问taobao被限，同一个ip第二次访问的请求可能在3s后返回；目前在压测location-service未替代方案
    

2. 测试对各业务模块未有较全的业务文档和用例，版本后需要增加相关文档'''
        cp.sendPlanSummaryEmail(planid, summary, issues, sender="", receiver="@.com", ccReceiver="", isSetFinish=True)

    @scenario(param={},
        where={})
    def testDailyReport(self):
        cp = CTestPlanAPi()
        planid = 5
        cp.sendPlandailyEmail(planid, day="2017-06-27", sender="", receiver="@.com", ccReceiver="")
    @scenario(param={},
        where={})
    def testGroupReport(self):
        cp = CTestPlanAPi()
        open("testplans.html", "wb").write(cp.getPlanReport(ptype="", inStatus=None, outStatus=3, fnid=6, nid1=6))
if __name__ == "__main__":
    from mtest import testing
    os.chdir("..")
    cprop.load("cplan.ini")
    testing("-r run  -i testDailyReport")
