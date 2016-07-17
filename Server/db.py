from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

Base = declarative_base()

#用户信息表
class DBUser(Base):

    __tablename__ = 'user'

    uid = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(Integer)
    mail = Column(String)
    sex = Column(Integer, default=0)
    authsuccess = Column(Integer, default=0)

    def __init__(self, username, password, mail, sex=0, authsuccess=0):

        self.username = username
        self.password = password
        self.mail = mail
        self.sex = sex
        self.authsuccess = authsuccess

    def __repr__(self):
        return "<user ('%s')>" % self.username

#群组表
class DBGroup(Base):

    __tablename__ = 'group'

    gid = Column(Integer, primary_key=True)
    groupname = Column(String)
    groupnumber = Column(Integer, default=0)

    def __init__(self, groupname, groupnumber=0):

        self.groupname = groupname
        self.groupnumber = groupnumber

#群组成员表
class DBGroupmember(Base):

    __tablename__ = 'groupmember'

    gmid = Column(Integer, primary_key=True)
    groupid = Column(Integer, ForeignKey('group.gid'))
    memberid = Column(Integer, ForeignKey('user.uid'))

    def __init__(self, groupid, memberid):

        self.groupid = groupid
        self.memberid = memberid

#邮箱表
class DBMail(Base):

    tablename__ = 'mailauth'

    mid = Column(Integer, primary_key=True)
    mail = Column(String)
    authword = Column(String)

    def __init__(self, mail, authword):

        self.mail = mail
        self.authword = authword

#离线添加好友信息
class DBOfflineAddFriend(Base):

    __tablename__ = 'offlineaddfriend'

    aid = Column(Integer, primary_key=True)
    fromid = Column(Integer, ForeignKey('user.uid'))
    toid = Column(Integer, ForeignKey('user.uid'))
    msg = Column(String)
    lastdate = Column(DateTime)

    def __init__(self, fid, tid, msg, dateTime):

        self.fromid = fid
        self.toid = tid
        self.msg = msg
        self.lastdate = dateTime

#好友关系表
class DBRelationship(Base):

    __tablename__ = 'relationship'

    rid = Column(Integer, primary_key=True)
    user1id = Column(Integer, ForeignKey('user.uid'))
    user2id = Column(Integer, ForeignKey('user.uid'))

    def __init__(self, u1id, u2id):

        self.user1id = u1id
        self.user2id = u2id

#缓存离线消息
class DBOfflineMsg(Base):

    __tablename__ = 'offlinemsg'

    oid = Column(Integer, primary_key=True)
    fromuserid = Column(Integer, ForeignKey('user.uid'))
    touserid = Column(Integer, ForeignKey('user.uid'))
    groupid = Column(Integer, ForeignKey('group.gid'))
    msg = Column(String)
    last_date = Column(DateTime)

    def __init__(self, fuid, touid, gid, msg, last_date):

        self.fromuserid = fuid
        self.touserid = touid
        self.groupid = gid
        self.msg = msg
        self.last_date = last_date


####################################################################################
##引擎
##数据库操作业务部分
####################################################################################
class DBEngine(object):

    def __init__(self):
        self.engine = create_engine('sqlite:///DB/chatdb.sqlite', echo=False)

        db_session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
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
    
    def register_new_user(self, username, password, mail, sex=0, authsuccess=0):

        user = DBUser(username=username, password=password, mail=mail, sex=sex, authsuccess=authsuccess)
        self.session.add(user)
        self.session.commit()

    def finish_new_user(self, mail):
        finisheduser = self.session.query(DBUser).filter(DBUser.mail == mail).first()
        finaluser = DBUser(finisheduser.username, finisheduser.password, finisheduser.mail, finisheduser.sex, 1)
        self.session.delete(finisheduser)
        self.session.add(finaluser)
        self.session.commit()

    def wirte_mail_auth(self, mail, authword):
        my_mail = DBMail(mail=mail, authword=authword)
        self.session.add(my_mail)
        self.session.commit()

    def getauthbymail(self, mail):
        return self.session.query(DBMail).filter(DBMail.mail == mail).first()

    def findIdWithName(self, username):
        return self.session.query(DBUser).filter(DBUser.username == username).first()

    def findNameWithId(self, uid):
        return self.session.query(DBUser).filter(DBUser.uid == uid).first()

    ####################################################################################
    #Group部分
    ####################################################################################
    def findGroupidWithGroupname(self, groupname):
        return self.session.query(DBGroup).filter(DBGroup.groupname == groupname).first()
    
    def register_new_group(self, groupname):
        group = DBGroup(groupname)
        self.session.add(group)
        self.session.commit()

    def get_group_number(self, groupname):
        gp = self.session.query(DBGroup).filter(DBGroup.groupname == groupname).first()
        return gp.groupnumber

    def get_all_group(self):
        return self.session.query(DBGroup)

    def get_list_group(self, uname):
        userid = self.findIdWithName(uname).uid
        return self.session.query(DBGroupmember).filter(DBGroupmember.memberid == userid)

    def get_group_member(self, groupname):
        gpid = self.findGroupidWithGroupname(groupname).gid
        return self.session.query(DBGroupmember).filter(DBGroupmember.groupid == gpid)

    def del_the_group(self, groupname):
        group = self.session.query(DBGroup).filter(DBGroup.groupname == groupname).first()
        self.session.delete(group)
        self.session.commit()
        
    def add_user_into_group(self, gname, uname):
        userid = self.findIdWithName(uname).uid
        groupid = self.findGroupidWithGroupname(gname).gid
        gmember = DBGroupmember(groupid, userid)
        gnumber = self.session.query(DBGroup).filter(DBGroup.groupname == gname).first().groupnumber
        self.session.query(DBGroup).filter(DBGroup.groupname == gname).update({'groupnumber': gnumber+1})
        self.session.add(gmember)
        self.session.commit()

    def del_user_from_group(self,gname, uname):
        userid = self.findIdWithName(uname).uid
        groupid = self.findGroupidWithGroupname(gname).gid
        print('groupid', groupid, 'userid', userid)
        gmember = self.session.query(DBGroupmember).filter(DBGroupmember.memberid == userid, DBGroupmember.groupid == groupid).first()
        print(gmember.groupid, gmember.memberid)
        gnumber = self.session.query(DBGroup).filter(DBGroup.groupname == gname).first().groupnumber
        self.session.query(DBGroup).filter(DBGroup.groupname == gname).update({'groupnumber': gnumber-1})
        self.session.delete(gmember)
        self.session.commit()

    def getGroupInfoWithGroupId(self, gid):
        return self.session.query(DBGroup).filter(DBGroup.gid == gid).first()

    ####################################################################################
    #数据库查看函数
    ####################################################################################
    def chakanDBUser(self):
        tems = self.session.query(DBUser)
        print('DBUser:')
        for tem in tems:
            print('   ', tem.uid,tem.username, tem.password, tem.mail, tem.authsuccess)
    def chakanDBOfflineAddFriend(self):
        tems = self.session.query(DBOfflineAddFriend)
        print('DBOfflineAddFriend:')
        print('   ', 'fromid', 'toid', 'msg', 'lastdate')
        for tem in tems:
            print('   ', tem.fromid, tem.toid, tem.msg, tem.lastdate)
    def chakanDBGroup(self):
        tems = self.session.query(DBGroup)
        print('DBGroup:')
        print('   ', 'gid', 'groupname', 'groupnumber')
        for tem in tems:
            print('   ', tem.gid, tem.groupname, tem.groupnumber)
    def chakanDBRelationship(self):
        tems = self.session.query(DBRelationship)
        print('DBRelationship:')
        print('   ', 'rid', 'user1id', 'user2id')
        for tem in tems:
            print('   ', tem.rid, tem.user1id, tem.user2id)
    def chakanDBOfflineMsg(self):
        tems = self.session.query(DBOfflineMsg)
        print('DBOfflineMsg:')
        for tem in tems:
            print('   ', tem.msg)
    def chakanDBGroupmember(self):
        tems = self.session.query(DBGroupmember)
        print('DBGroupmember:')
        for tem in tems:
            print('   ', tem.groupid, tem.memberid)
    ####################################################################################
    #friends
    ####################################################################################

    #是否已存在好友关系
    def getFriendshipWithUserFriendName(self, uname, fname):

        userid = self.findIdWithName(uname).uid
        friendid = self.findIdWithName(fname).uid
        friendship = self.session.query(DBRelationship).filter(DBRelationship.user1id == userid, DBRelationship.user2id == friendid).first()
        if friendship:
            return friendship
        friendship = self.session.query(DBRelationship).filter(DBRelationship.user1id == friendid, DBRelationship.user2id == userid).first()

        return friendship


    #保存好友关系
    def setFriendshipWithUserNames(self, uname, fname):

        userid = self.findIdWithName(uname).uid
        friendid = self.findIdWithName(fname).uid
        relationship = DBRelationship(userid, friendid)
        self.session.add(relationship)
        self.session.commit()

    #根据用户name获取资料
    def getUserInfoWithUserName(self, uname):

        return self.session.query(DBUser).filter(DBUser.username == uname).first()

    #根据用户id获取资料
    def getUserInfoWithUserId(self, userId):

        return self.session.query(DBUser).filter(DBUser.uid == userId).first()

    #根据用户name获取好友
    def getUserFriendshipWithUserName(self, uname):

        userId = self.findIdWithName(uname).uid
        user1Friend = self.session.query(DBRelationship).filter(DBRelationship.user1id == userId)
        user2Friend = self.session.query(DBRelationship).filter(DBRelationship.user2id == userId)

        return user1Friend, user2Friend

    #根据用户name获取所有离线申请好友信息
    def getOfflineAddFriendRequests(self , uname):

        userid = self.findIdWithName(uname).uid
        return self.session.query(DBOfflineAddFriend).filter(DBOfflineAddFriend.toid == userid)

    #根据用户name删除离线好友请求
    def deleteOfflineAddFriendRequestWithUserName(self, uname):

        userId = self.findIdWithName(uname).uid
        offlineAddRequests = self.session.query(DBOfflineAddFriend).filter(DBOfflineAddFriend.toid == userId)
        for offlineAddReq in offlineAddRequests:
            self.session.delete(offlineAddReq)

        self.session.commit()

    #保存添加请求,当前好友状态为离线
    def setOfflineAddFriendReuqest(self, fname, uname, msg, dateTime):

        fid = self.findIdWithName(fname).uid
        uid = self.findIdWithName(uname).uid
        offline_add_request = self.session.query(DBOfflineAddFriend).filter(DBOfflineAddFriend.toid == fid, DBOfflineAddFriend.fromid == uid).first()
        if offline_add_request:
            self.session.query(DBOfflineAddFriend).filter(DBOfflineAddFriend.toid == fid, DBOfflineAddFriend.fromid == uid).update({'msg':msg, 'lastdate':dateTime})
        else:
            offline_add_request = DBOfflineAddFriend(uid, fid, msg, dateTime)
        self.session.add(offline_add_request)

        self.session.commit()

    #根据用户name和好友name删除好友关系
    def deleteFriendshipByUserAndFriendName(self , uname, fname):

        userId = self.findIdWithName(uname).uid
        friendId = self.findIdWithName(fname).uid
        user1Friend = self.session.query(DBRelationship).filter(DBRelationship.user1id == userId ,DBRelationship.user2id == friendId).first()
        if not user1Friend:
            user1Friend = self.session.query(DBRelationship).filter(DBRelationship.user1id == friendId ,DBRelationship.user2id == userId).first()

        self.session.delete(user1Friend)
        self.session.commit()


    ####################################################################################
    #chat
    ####################################################################################

    #根据用户name获取离线信息
    def getAllOfflineChatMessageWithUserName(self, uname):

        userId = self.findIdWithName(uname).uid
        return self.session.query(DBOfflineMsg).filter(DBOfflineMsg.touserid  == userId)

    #根据用户name删除所有离线信息
    def deleteAllOfflineChatMessageWithUserName(self, uname):

        userId = self.findIdWithName(uname).uid
        offlineChatMessage = self.session.query(DBOfflineMsg).filter(DBOfflineMsg.touserid == userId)
        for offlineChatMsg in offlineChatMessage:
            self.session.delete(offlineChatMsg)

        self.session.commit()

    #保存离线聊天消息
    def addOfflineChatMessageWithUserName(self, uname, fname, gname, message, lastdate):

        userId = self.findIdWithName(uname).uid
        friendId = self.findIdWithName(fname).uid
        groupId = self.findGroupidWithGroupname(gname).gid
        offChatMsg = DBOfflineMsg(userId, friendId, groupId, message, lastdate)
        self.session.add(offChatMsg)
        self.session.commit()

if __name__ == '__main__':
    my_db = DBEngine()
    #初始化数据库
    #Base.metadata.create_all(my_db.engine)
    #my_db.register_new_group('')
    #my_db.register_new_group('test')
    #my_db.register_new_group('test2')
    
    #my_db.deleteFriendshipByUserAndFriendName('willin','vedream')
    #my_db.deleteFriendshipByUserAndFriendName('willin','willing')
    #my_db.deleteFriendshipByUserAndFriendName('willing','vedream')
    #my_db.deleteFriendshipByUserAndFriendName('willing','wuyuan')
    #my_db.deleteFriendshipByUserAndFriendName('wuyuan','vedream')
    #my_db.deleteFriendshipByUserAndFriendName('willin','wuyuan')
    #my_db.
    #查看数据库DBUser
    my_db.chakanDBUser()
    #查看数据库DBOfflineAddFriend
    my_db.chakanDBOfflineAddFriend()
    #查看数据库DBGroup
    my_db.chakanDBGroup()
    #查看数据库DBRelationship
    my_db.chakanDBRelationship()
    #查看数据库DBOfflineMsg
    my_db.chakanDBOfflineMsg()
    #查看数据库DBGroup
    my_db.chakanDBGroupmember()