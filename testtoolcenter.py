# -*- coding: utf8 -*-
'''
Created on 2016-10-2

@author: chinple
'''
from cserver import  cloudModule
from db.sqltool import  BasicSqlTool
from server.chandle import ReturnFileException

@cloudModule()
class ShowSqltable(BasicSqlTool):
    def __init__(self, isCheckUpdate=True, isSupportDelete=False, isSupportAnySql=False, dbstoreName="dbstore"):
        BasicSqlTool.__init__(self, isCheckUpdate, isSupportDelete, isSupportAnySql, dbstoreName)

        self.tableTemplate = open("datas/showtabletemplate.html").read()
        self.sqls = {}

    def _getWidth(self, widths, i):
        try:
            return " width=%s" % widths[i]
        except:return ""

    def _formatRow(self, r, widths=None):
        rs = []
        i = 0
        for d in r:
            i += 1
            d = str("" if d is None else d).replace("<", "&lt;").replace(">", "&gt;")
            if widths is None:
                rs.append("<td>%s</td>" % d)
            else:
                rs.append("<td%s>%s</td>" % (self._getWidth(widths, i), d))
        return "".join(rs)
    
    def addQuery(self, sqlkey, sqlStr, widths):
        self.sqls[sqlkey] = (sqlStr, widths.replace(",", " ").split())
        return self.sqls.keys()

    tryAgain = True
    def showtable(self, dbconfig, sql):
        if self.sqls.__contains__(sql):
            sql, widths = self.sqls[sql]
        else:
            return "No such sql"
        try:
            sqlConn = self.__getConn__(dbconfig)
            res = sqlConn.executeSql(sql, isFethall=False)
            rows = []
            try:
                head = self._formatRow([h[0] for h in res.description], widths)
                while True:
                    r = res.fetchone()
                    if r is None:
                        break
                    rows.append("<tr>%s</tr>" % self._formatRow(r))
            finally: res.close()
            self.tryAgain = True
        except:
            self.executeSql(dbconfig=dbconfig)
            if self.tryAgain:
                self.tryAgain = False
                return self.showtable(dbconfig, sql)

        maxWidth = self._getWidth(widths, 0)
        d = self.tableTemplate.replace("{maxWidth}", maxWidth).replace("{head}", head).replace("{content}", "".join(rows))
        raise ReturnFileException(d, 'text/html')

if __name__ == "__main__":
    from cserver import servering
    servering("-p 8089 -f webs  -m CToolPlatform.html ")
