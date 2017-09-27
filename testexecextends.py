class BugFreeApi:
    def __init__(self):
#         sqlConfig = {'host':cprop.getVal("bugfree", "host"), 'port':cprop.getInt("bugfree", "port"),
#             'user':cprop.getVal("bugfree", "user"), 'passwd':cprop.getVal("bugfree", "passwd"),
#             'db':cprop.getVal("bugfree", "db"), 'charset':'utf8'}
#         self.sqlConn = SqlConnFactory(MysqldbConn, sqlConfig)
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
