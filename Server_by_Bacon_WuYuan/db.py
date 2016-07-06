from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

Base = declarative_base()

class DBUser(Base):
    """
    用户信息
    """
    __tablename__ = 'user'

    uid         = Column(Integer, primary_key = True)
    username    = Column(String)
    password    = Column(Integer)
    mail		= Column(String)
    sex         = Column(Integer, default = 0)
    authsuccess = Column(Integer, default = 0)

    def __init__(self, username, password, mail, sex = 0, authsuccess = 0):

        self.username = username
        self.password = password
        self.mail = mail
        self.sex = sex
        self.authsuccess = authsuccess


    def __repr__(self):
        return "<user ('%s')>" % (self.username)

class DBMail(Base):
	"""
	邮箱表
	"""
	__tablename__ = 'mailauth'

	mid          = Column(Integer, primary_key = True)
	mail         = Column(String)
	authword     = Column(String)

	def __init__(self, mail, authword):
		
		self.mail = mail
		self.authword = authword

class DBOfflineAddFriend(Base):
    """
    离线添加好友消息
    """

    __tablename__ = 'offlineaddfriend'

    aid         = Column(Integer, primary_key=True)
    fromid      = Column(Integer, ForeignKey('user.uid'))
    toid        = Column(Integer, ForeignKey('user.uid'))
    msg         = Column(String)
    lastdate    = Column(DateTime)

    def __init__(self, fid, tid, msg, dateTime):
        """
        赋值
        """
        self.fromid = fid
        self.toid = tid
        self.msg = msg
        self.lastdate = dateTime


class DBRelationship(Base):
    """
    好友关系表
    """

    __tablename__ = 'relationship'

    rid         = Column(Integer, primary_key=True)
    user1id     = Column(Integer, ForeignKey('user.uid'))
    user2id     = Column(Integer, ForeignKey('user.uid'))


    def __init__(self , u1id, u2id):

        self.user1id = u1id
        self.user2id = u2id


class DBOfflineMsg(Base):
    """
    缓存离线消息
    """

    __tablename__ = 'offlinemsg'

    oid         = Column(Integer, primary_key=True)
    fromuserid  = Column(Integer, ForeignKey('user.uid'))
    touserid    = Column(Integer, ForeignKey('user.uid'))
    msg         = Column(String)
    last_date   = Column(DateTime)

    def __init__(self , fuid, touid, msg, last_date):

        self.fromuserid = fuid
        self.touserid = touid
        self.msg = msg
        self.last_date = last_date


class DBEngine(object):
    """
    数据库操作业务部分
    当前数据库操作没有异常处理和错误校验，正式发行时候应该添加上
    """

    def __init__(self):
        self.engine = create_engine('sqlite:///DB/chatdb.sqlite', echo = False)

        db_session = sessionmaker(autocommit=False,autoflush=False,bind=self.engine)
        self.session = db_session()

    def closeDB(self):

        self.session.close()

    ####################################################################################
    #user部分
    ####################################################################################
    def isUserExist(self, username, password):

        return self.session.query(DBUser).filter(DBUser.username == username, DBUser.password == password).first()

    def isMailExist(self, mail):

        return self.session.query(DBMail).filter(DBMail.mail == mail).first()
    
    def register_new_user(self, username, password, mail, sex = 0,authsuccess = 0):

        user = DBUser(username = username, password = password, mail = mail, sex = sex, authsuccess =authsuccess)
        self.session.add(user)
        self.session.commit()

    def finish_new_user(self, mail):
        finisheduser = self.session.query(DBUser).filter(DBUser.mail == mail).first()
        finaluser = DBUser(finisheduser.username,finisheduser.password,finisheduser.mail,finisheduser.sex,1)
        self.session.delete(finisheduser)
        self.session.add(finaluser)
        self.session.commit()

    def wirte_mail_auth(self, mail, authword):
        my_mail = DBMail(mail = mail, authword = authword)
        self.session.add(my_mail)
        self.session.commit()

    def getauthbymail(self, mail):
        return self.session.query(DBMail).filter(DBMail.mail == mail).first()

    def findIdWithName(self, username):
    	return self.session.query(DBUser).filter(DBUser.username == username).first()

    def findNameWithId(self, uid):
        return self.session.query(DBUser).filter(DBUser.uid == uid).first()
    ####################################################################################
    #friends
    ####################################################################################

    def getFriendshipWithUserFriendName(self, uname, fname):
        """
        是否已经存在好友关系
        """
        userid = self.findIdWithName(uname).uid
        friendid = self.findIdWithName(fname).uid
        friendship = self.session.query(DBRelationship).filter(DBRelationship.user1id == userid, DBRelationship.user2id == friendid).first()
        if friendship:
            return friendship
        friendship = self.session.query(DBRelationship).filter(DBRelationship.user1id == friendid, DBRelationship.user2id == userid).first()

        return friendship



    def setFriendshipWithUserNames(self, uname, fname):
        """
        保存好友关系
        """
        userid = self.findIdWithName(uname).uid
        friendid = self.findIdWithName(fname).uid
        relationship = DBRelationship(userid, friendid)
        self.session.add(relationship)
        self.session.commit()


    def getUserInfoWithUserName(self, uname):
        """
        根据用户name，获取用户资料
        """
        return self.session.query(DBUser).filter(DBUser.username == uname).first()

    def getUserInfoWithUserId(self, userId):
        """
        根据用户id，获取用户资料
        """
        return self.session.query(DBUser).filter(DBUser.uid == userId).first()

    def getUserFriendshipWithUserName(self, uname):
        """
        根据用户name，获取用户好友
        """
        userId = self.findIdWithName(uname).uid
        user1Friend = self.session.query(DBRelationship).filter(DBRelationship.user1id == userId)
        user2Friend = self.session.query(DBRelationship).filter(DBRelationship.user2id == userId)

        return user1Friend, user2Friend



    def getOfflineAddFriendRequests(self , uname):
        """
        根据用户name，获取所有离线申请添加好友的信息
        """
        userid = self.findIdWithName(uname).uid
        return self.session.query(DBOfflineAddFriend).filter(DBOfflineAddFriend.toid == userid)


    def deleteOfflineAddFriendRequestWithUserName(self, uname):
        """
        根据用户name，删除离线好友请求
        """
        userId = self.findIdWithName(uname).uid
        offlineAddRequests = self.session.query(DBOfflineAddFriend).filter(DBOfflineAddFriend.toid == userId)
        for offlineAddReq in offlineAddRequests:
            self.session.delete(offlineAddReq)

        self.session.commit()


    def setOfflineAddFriendReuqest(self, fname, uname, msg, dateTime):
        """
        保存添加请求，当前好友为离线状态
        """
        fid = self.findIdWithName(fname).uid
        uid = self.findIdWithName(uname).uid
        offline_add_request = self.session.query(DBOfflineAddFriend).filter(DBOfflineAddFriend.toid == fid, DBOfflineAddFriend.fromid == uid).first()
        if offline_add_request:
            self.session.query(DBOfflineAddFriend).filter(DBOfflineAddFriend.toid == fid, DBOfflineAddFriend.fromid == uid).update({'msg':msg, 'lastdate':dateTime})
        else:
            offline_add_request = DBOfflineAddFriend(uid, fid, msg, dateTime)
        self.session.add(offline_add_request)

        self.session.commit()


    def deleteFriendshipByUserAndFriendName(self , uname, fname):
        """
        根据用户name和好友name删除好友关系
        """
        userID = self.findIdWithName(uname).uid
        friendId = self.findIdWithName(fname).uid
        user1Friend = self.session.query(DBRelationship).filter(DBRelationship.user1id == userId ,DBRelationship.user2id == friendId).first()
        if not user1Friend:
            user1Friend = self.session.query(DBRelationship).filter(DBRelationship.user1id == friendId ,DBRelationship.user2id == userId).first()

        self.session.delete(user1Friend)
        self.session.commit()


    ####################################################################################
    #chat
    ####################################################################################

    def getAllOfflineChatMessageWithUserName(self, uname):
        """
        根据用户name，获取所有离线消息
        """
        userId = self.findIdWithName(uname).uid
        return self.session.query(DBOfflineMsg).filter(DBOfflineMsg.touserid  == userId)


    def deleteAllOfflineChatMessageWithUserName(self, uname):
        """
        根据用户name，删除所有离线消息
        """
        userId = findIdWithName(uname).uid
        offlineChatMessage = self.session.query(DBOfflineMsg).filter(DBOfflineMsg.touserid == userId)
        for offlineChatMsg in offlineChatMessage:
            self.session.delete(offlineChatMsg)

        self.session.commit()


    def addOfflineChatMessageWithUserName(self, uname, fname, message, lastdate):
        """
        保存离线聊天消息
        """
        userId = self.findIdWithName(uname).uid
        friendId = self.findIdWithName(fname).uid
        offChatMsg = DBOfflineMsg(userId, friendId, message, lastdate)
        self.session.add(offChatMsg)
        self.session.commit()

if __name__ == '__main__':
    my_db = DBEngine()
    Base.metadata.create_all(my_db.engine)
    #my_db.register_new_user("wuyuan","pearlismylove",0)
    #tem = my_db.isUserExist("caonima1",895640624)
    # print (tem.authsuccess)
    # a = my_db.getauthbymail(tem.mail)
    # print (a.authword)
    #my_db.finish_new_user(tem.mail)
    # tem2 = my_db.isUserExist("caonima1",895640624)
    #print (tem2.authsuccess)
    #print (tem.description)
    #tem2 = A("wuyuan",120)
    #print (tem2.name)