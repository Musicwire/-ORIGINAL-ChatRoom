import datetime
import json
import smtplib
import random
from email.mime.text import MIMEText

from db import DBEngine, DBUser, DBRelationship, DBOfflineMsg, DBOfflineAddFriend, DBMail
from models import ServeList, GroupObject, UserObject, USERS_PAGES_SIZE
from protocol import PackageLogin, PackageRegister, PackageRegisterAuth, PackageAddFriendRequest, PackageAddFriendStatus , PackageGetFriends , PackageDeleteFriend , PackageGetFriendDetail , PackageSendChatMessage, PackageExitGroup, PackageJoinGroup, PACKAGE_ERRCODE_INPUTWRONG,PACKAGE_ERRCODE_LENGTHTOSHORT,PACKAGE_ERRCODE_USERISEXIST, PACKAGE_ERRCODE_AUTHFAILED, PACKAGE_ERRCODE_LENGTHTOSHORT , PACKAGE_ERRCODE_FRIENDSHIPEXIST , PACKAGE_ERRCODE_USERFRIENDID, PACKAGE_ERRCODE_MAILNOTCONFIRM, PACKAGE_ERRCODE_NOTHISUSER, PACKAGE_ERRCODE_ANOTHERLOGIN, PACKAGE_ERRCODE_USERID, PACKAGE_ERRCODE_USEDMAIL, PACKAGE_ERRCODE_USERUNEXIST, PACKAGE_ERRCODE_INGROUP, PACKAGE_ERRCODE_NOTINGROUP, ComplexEncoder, SendToClientPackage, SendToClientPackageUser, SendToClientPackageChatMessage, SendToClientPackageRecvAddFriendRequest, SendToClientAddFriendStatus, SendToClientUserOnOffStatus, SendToClientGroupMemberJoinExitStatus


class Logic(object):

    def __init__(self):
        self.serverList = ServeList()
        self.dbEngine = DBEngine()
        self.groupInit()

    def findBadInput(self, inputstring):
        #输入是否合法，防止sql注入#
        if '\'' in inputstring:
            return True
        elif '\"' in inputstring:
            return True
        elif '`' in inputstring:
            return True
        elif ' ' in inputstring:
            return True

    def groupInit(self):
        pass
        # db_groups = self.dbEngine.所有的群组名()
        #
        # for db_group in db_groups:
        #     group = GroupObject(db_group)
        #     self.serverList.addNewGroup(group)
        #
        #     self.getGroupMemberWithDB(group)

    def reset(self):
        self.serverList.reset()

    ####################################################################################
    # 一.协议处理部分
    ####################################################################################

    ##逻辑处理部分##
    def handlePackage(self, connection , package):
        if isinstance(package, PackageRegister):
            self.handleUserRegister(connection, package)

        elif isinstance(package, PackageRegisterAuth):
            self.handleUserRegisterAuth(connection, package)

        elif isinstance(package, PackageLogin):
            self.handleUserLogin(connection, package)

        elif isinstance(package, PackageAddFriendRequest):
            self.handleAddFriendRequest(connection, package)

        elif isinstance(package, PackageAddFriendStatus):
            self.handleAddFriendRequestStatus(connection, package)

        elif isinstance(package, PackageGetFriends):
            self.handleGetFriends(connection, package)

        elif isinstance(package, PackageDeleteFriend):
            self.handleDeleteFriend(connection, package)

        elif isinstance(package, PackageGetFriendDetail):
            self.handleGetFriendDetail(connection, package)

        elif isinstance(package, PackageSendChatMessage):
            self.handleSendChatMessage(connection, package)

        elif isinstance(package, PackageJoinGroup):
            self.handleJoinGroup(package)

        elif isinstance(package, PackageExitGroup):
            self.handleExitGroup(package)

    def closeConnection(self, connection):
        print("closeConnection OK")
        user = self.serverList.getUserByConnection(connection)
        if user:#注册完成之后就断开socket
            self.serverList.deleteUserByUser(user)
            friends = user.getAllFriends()
            if len(friends) > 0:
                self.broadcastOnlineStatusToAllFriend(user, 0)

    ####################################################################################
    #逻辑处理
    ####################################################################################


    #----用户注册处理----#
    def handleUserRegister(self, connection, package):

        retPackage = SendToClientPackage('register')

        #step 1，检查参数合法性
        if self.findBadInput(package.username):
            #帐号异常#
            retPackage.errcode = PACKAGE_ERRCODE_INPUTWRONG

        #step 2，检查参数长度
        elif len(package.username) < 5 or len(package.username) > 13:
            #长度太小#
            retPackage.errcode = PACKAGE_ERRCODE_LENGTHTOSHORT

        else:
            #step 3，检查用户是否存在
            db_user = self.dbEngine.isUserExist(package.username, package.password)

            #已经存在用户，返回重新注册
            if db_user:
                retPackage.errcode = PACKAGE_ERRCODE_USERISEXIST

            #不存在,插入数据库
            else:
                #检查邮箱是否已经被注册
                db_mail = self.dbEngine.isMailExist(package.mail)
                if db_mail:
                    retPackage.errcode = PACKAGE_ERRCODE_USEDMAIL
                else:
                    #发送验证码至邮箱
                    print ('authcode')
                    authcode = self.getauthcode()
                    self.dbEngine.wirte_mail_auth(package.mail,authcode)
                    self.sendmailauth(package.mail,authcode)

                    #将该验证码存至数据库
                    self.dbEngine.register_new_user(package.username, package.password, package.mail, package.sex)
                    retPackage.status = 1

        connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

    #----用户注册验证----#
    def handleUserRegisterAuth(self,connection, package):

        retPackage = SendToClientPackage('registerauth')
        #step 1 #
        correctcode = self.dbEngine.getauthbymail(package.mail)
        print(correctcode.authword)
        print(package.auth)
        if correctcode.authword == package.auth:
            retPackage.status = 1
            #修改数据库
            self.dbEngine.finish_new_user(package.mail)
            print('change')
        else:
            retPackage.errcode = PACKAGE_ERRCODE_AUTHFAILED
        #step 2
        connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))


    #----用户登录处理----#
    def handleUserLogin(self, connection, package):

        retPackage = SendToClientPackage('login')

        #step 1，检查参数合法性
        if self.findBadInput(package.username):
            retPackage.errcode = PACKAGE_ERRCODE_INPUTWRONG

        else:
            #step 2. 查询数据库
            db_user = self.dbEngine.isUserExist(package.username, package.password)

            if not db_user:
                #用户不存在，提醒注册
                retPackage.errcode = PACKAGE_ERRCODE_USERUNEXIST

            elif db_user.authsuccess == 0:
                retPackage.errcode = PACKAGE_ERRCODE_MAILNOTCONFIRM

            else:
                #step 1. 枚举在线用户，如果在线，退掉
                online_user = self.serverList.getUserExistByUsername(package.username)
                if online_user:
                    #step 1.发送异地登录消息
                    another = SendToClientPackage('anotherlogin')
                    another.errcode = PACKAGE_ERRCODE_ANOTHERLOGIN

                    online_user.connection.send_message(json.dumps(another, cls=ComplexEncoder))

                    #step 2.关闭联接
                    online_user.connection.close()

                #重新加入到在线用户
                user = UserObject(connection, db_user)
                self.serverList.addNewOnlineUser(user)

                retPackage.status = 1
                retPackage.obj = SendToClientPackageUser(user.DBUser.username,
                                                         user.DBUser.sex,
                                                         user.DBUser.mail,
                                                         True)
                #加载好友列表
                self.getUserFriendsWithDBAndOnLineUsers(user)

                #检查离线消息，是否有人希望添加我为好友
                self.getAllAddFriendRequestFromDBAndSendToClient(user)

                #是否有发给我的离线消息
                self.getOfflineChatMessageAndSendWithUser(user)

                #广播好友列表，通知本人上线
                self.broadcastOnlineStatusToAllFriend(user, 1)

                #修改在线列表,本人上线
                self.setUserOnlineInOnlineUsersFriends(user)

        connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))


    #----转发好友申请----#
    def handleAddFriendRequest(self, connection, package):

        user = self.serverList.getUserByConnection(connection)
        retPackage = SendToClientPackage('addfriend')
        bFriendship = False

        #检查是否是自己并且不是自己想要添加自己为好友
        if user.DBUser.username == package.username and user.DBUser.username != package.friendname:
            friend = user.getFriendWithUserName(package.fiendname)

            if friend:
                bFriendship = True

            if not bFriendship:
                retPackage.status = 1
                user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

                #step2 在线,发送添加
                online_user = self.serverList.getUserExistByUsername(package.friendname)

                if online_user:
                    addreq = SendToClientPackageRecvAddFriendRequest(package.username,
                                                                     package.friendname,
                                                                     user.DBUser.sex,
                                                                     package.msg,
                                                                     package.msg, datetime.datetime.now())
                    retPackage.obj = addreq

                    online_user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
                else:
                    #插入数据库,等待上线时候通知
                    self.dbEngine.setOfflineAddFriendReuqest(package.username, package.friendname, package.msg, datetime.datetime.now())

            else:
                #已经是好友，返回错误信息
                retPackage.errcode = PACKAGE_ERRCODE_FRIENDSHIPEXIST
                user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

        else:
            #用户ID错误，或者用户ID等于好友ID
            retPackage.errcode = PACKAGE_ERRCODE_USERFRIENDID
            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))


    #---应答是否同意添加好友请求---#
    def handleAddFriendRequestStatus(self, connection, package):

        user = self.serverList.getUserByConnection(connection)
        retPackage = SendToClientPackage('addfriendstatus')

        #自己的id
        if user.DBUser.username == package.username and user.DBUser.username != package.friendname:

            #如果同意
            if package.agree:

                #step 1. 检查是否是自己的好友
                if not self.dbEngine.getFriendshipWithUserFriendId(package.uid, package.fid):
                    db_friend = self.dbEngine.getUserInfoWithUserId(package.fid)

                    #存在数据库中
                    if db_friend:
                        retPackage.status = 1
                        #保存关系到数据库
                        self.dbEngine.setFriendshipWithUserNames(package.username, package.friendname)

                        user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
                        #检查是否在线,在线发送上线通知
                        online_friend = self.serverList.getUserExistByUsername(package.friendname)

                        if online_friend:
                            #当前在线
                            online_status = SendToClientAddFriendStatus(package.username,
                                                                        package.friendname,
                                                                        user.DBUser.sex,
                                                                        package.msg,
                                                                        package.agree)
                            retPackage.obj = online_status
                            #发送有人添加好友申请
                            online_friend.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

                            #添加到我的好友列表
                            user.addFriend(online_friend)
                        else:
                            #此处应该添加系统回复消息至数据库
                            #用户上线时，将此消息发送
                            pass

                    else:
                        retPackage.errcode = PACKAGE_ERRCODE_NOTHISUSER

                        #返回添加好友状态
                        user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

                else:
                    #已经是好友提示
                    retPackage.errcode = PACKAGE_ERRCODE_FRIENDSHIPEXIST

                    user.connection.send_message(json.dumps(retPackage, cls= ComplexEncoder))

            else:
                #返回状态
                retPackage.status = 1
                #返回添加好友状态
                user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

                #TODO:拒绝不提示
                pass

        else:
            #用户ID异常
            retPackage.errcode = PACKAGE_ERRCODE_USERFRIENDID
            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))


    #---获取好友列表---#
    def handleGetFriends(self, connection, package):

        user = self.serverList.getUserByConnection(connection)
        retPackage = SendToClientPackage('getfriends')

        #自己的name
        if user.DBUser.username == package.username:

            retFriend = self.getUserFriendsWithUserAndPage(user, int(package.page))

            if len(retFriend) > 0:
                retPackage.obj = retFriend

            retPackage.status = 1

        else:
            retPackage.errcode = PACKAGE_ERRCODE_USERID
        print('getfriends')
        user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))


    # ---获得好友信息---#
    def handleGetFriendDetail(self, connection, package):

        user = self.serverList.getUserByConnection(connection)
        retPackage = SendToClientPackage('getfrienddetail')

        #自己的id
        if user.DBUser.uid == int(package.uid) and user.DBUser.uid != int(package.fid):
            retPackage.status = 1

            #获取用户详细资料返回

        else:
            retPackage.errcode = PACKAGE_ERRCODE_USERID
            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))


    #---删除好友---#
    def handleDeleteFriend(self, connection, package):

        user = self.serverList.getUserByConnection(connection)
        retPackage = SendToClientPackage('delfriend')

        #自己的id
        if user.DBUser.username == int(package.username) and user.DBUser.username != int(package.friend):
            retPackage.status = 1

            #从数据库中删除
            self.dbEngine.deleteFriendshipByUserAndFriendId(package.username, package.friend)

            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

            #给在线好友发送通知，删除
            online_friend = self.serverList.getUserExistByUsername(package.friend)
            if online_friend:
                sendObj = SendToClientPackageUser(user.DBUser.username,
                                                  user.DBUser.sex,
                                                  user.DBUser.mail)
                retPackage.obj = sendObj
                online_friend.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

                #从维护的好友列表中删除
                user.deleteFriend(online_friend)

        else:
            retPackage.errcode = PACKAGE_ERRCODE_USERID
            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))


    # ---加入群组---#
    def handleJoinGroup(self, package):

        user = self.serverList.getUserByUsername(package.username)
        group = self.serverList.getGroupByUsername(package.groupname)
        retPackage = SendToClientPackage('joingroup')

        # step 1. 检查未入群
        if not user.DBUser.username in self.serverList.group[package.groupname].members:

            #添加到群组成员表中
            group.addMember(user)

            #保存关系到数据库
            self.dbEngine.保存入库
            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

            #广播进退群消息
            self.broadcastJoinExitStatusToAllMember(package.username, package.groupname, package.status)

        #已经在群里
        else:
            retPackage.errcode = PACKAGE_ERRCODE_INGROUP
            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))


    # ---退出群组---#
    def handleExitGroup(self, package):

        user = self.serverList.getUserByUsername(package.username)
        group = self.serverList.getGroupByUsername(package.groupname)
        retPackage = SendToClientPackage('exitgroup')

        #在群里
        if user.DBUser.username in self.serverList.group[package.groupname].members:

            #更新群组成员列表
            group.deleteMember(user)

            # 从数据库中删除
            self.删除群成员()
            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

            # 广播进退群消息
            self.broadcastJoinExitStatusToAllMember(package.username, package.groupname, package.status)

        #不在群里
        else:
            retPackage.errcode = PACKAGE_ERRCODE_NOTINGROUP
            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))


    # ---发送聊天消息---#
    def handleSendChatMessage(self, connection, package):

        user = self.serverList.getUserByConnection(connection)
        retPackage = SendToClientPackage('sendchatmsg')

        # 不是群组消息
        if package.groupname is None:

            # 自己的name
            if user.DBUser.username == package.fromname and user.DBUser.username != package.toname:

                #寻找好友
                for friend in user.getAllFriends():

                    if friend.DBUser.username == int(package.toname):
                        #发送消息给好友
                        retPackage.status = 1

                        user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

                        chat = SendToClientPackageChatMessage(package.fromname,
                                                              package.toname,
                                                              '',
                                                              package.chatmsg,
                                                              datetime.datetime.now())
                        retPackage.obj = chat
                        if friend.connection:
                            friend.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
                        else:
                            #当前不在线，数据库插入离线消息
                            self.dbEngine.addOfflineChatMessageWithUserName(package.fromname,
                                                                            package.toname,
                                                                            '',
                                                                            package.chatmsg,
                                                                            datetime.datetime.now())
                        return
            else:
                retPackage.errcode = PACKAGE_ERRCODE_USERID
                user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

        # 是群组消息
        else:

            # 判断自己在群内
            if user.DBUser.username in self.serverList.group[package.groupname].members:

                # 寻找群内成员
                for member in self.serverList.group[package.groupname].members():

                    #广播消息给群组成员
                    retPackage.status = 1

                    user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

                    chat = SendToClientPackageChatMessage(package.fromname,
                                                          '',
                                                          package.groupname,
                                                          package.chatmsg,
                                                          datetime.datetime.now())
                    retPackage.obj = chat
                    if member.connection:
                        member.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
                    else:
                        # 当前不在线，数据库插入离线消息
                        self.dbEngine.addOfflineChatMessageWithUserName(package.fromname,
                                                                        member.username,
                                                                        package.groupname,
                                                                        package.chatmsg,
                                                                        datetime.datetime.now())
                    return
            else:
                retPackage.errcode = PACKAGE_ERRCODE_NOTINGROUP
                user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))


    ####################################################################################
    #逻辑中的部分细节处理
    ####################################################################################

    #---生成认证码---#
    #---from:handleUserRegister---#
    def getauthcode(self):
        authcode = ''
        for i in range (4):
            authcode += random.choice('abcdefghijklmnopqrstuvwxyz')
        return authcode


    #---发送邮箱认证码---#
    #---from:handleUserRegister---#
    def sendmailauth(self, mail, authcode):
        smtp_server = 'smtp.sina.com'
        username = 'wywhy_private@sina.com'
        password = 'wywhy123456'
        from_addr = 'wywhy_private@sina.com'
        to_addr = mail
        message = 'authcode:' + authcode
        msg = MIMEText(message, 'plain', 'utf-8')
        server = smtplib.SMTP(smtp_server, 25)
        #server.set_debuglevel(1)
        server.login(username, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
        server.quit()


    #---获取用户的所有好友信息---#
    #---from:handleUserLogin---#
    def getUserFriendsWithDBAndOnLineUsers(self, user):

        #step 1.从数据库加载
        (user1Friends, user2Friends) = self.dbEngine.getUserFriendshipWithUserName(user.DBUser.username)

        for friend in user1Friends:
            db_user = self.dbEngine.getUserInfoWithUserId(friend.user2id)
            friend = UserObject(None, db_user)
            user.addFriend(friend)
            online_friend = self.serverList.getUserExistByUsername(db_user.username)
            if online_friend:
                friend.connection = online_friend.connection
                friend.online = True

        for friend in user2Friends:
            db_user = self.dbEngine.getUserInfoWithUserId(friend.user1id)
            friend = UserObject(None, db_user)
            user.addFriend(friend)
            online_friend = self.serverList.getUserExistByUsername(db_user.username)
            if online_friend:
                friend.connection = online_friend.connection
                friend.online = True


    # ---获取群组的所有成员信息---#
    # ---from:groupInit---#
    def getGroupMemberWithDB(self, group):

        members = self.dbEngine.获得群组所有成员(group.DBGroup.groupname)

        for member in members:
            db_user = self.dbEngine.getUserInfoWithUserName(member.username)
            member = UserObject(db_user)
            group.addMember(member)


    #---从数据库获取所有离线申请添加好友的用户并发送给用户--#
    #---from:handleUserLogin---#
    def getAllAddFriendRequestFromDBAndSendToClient(self, user):

        add_requests = []
        offline_add_friend_requests = self.dbEngine.getOfflineAddFriendRequests(user.DBUser.username)
        for off_add_req in offline_add_friend_requests:

            fuser = self.dbEngine.getUserInfoWithUserId(off_add_req.fromid)
            send_request = SendToClientPackageRecvAddFriendRequest(fuser.username,
                                                                   user.DBUser.username,
                                                                   off_add_req.msg,
                                                                   off_add_req.lastdate)
            add_requests.append(send_request)

        if len(add_requests) > 0:
            #发送
            retRequest = SendToClientPackage('addfriend')
            retRequest.status = 1
            retRequest.obj = add_requests

            user.connection.send_message(json.dumps(retRequest, cls=ComplexEncoder))

            #删除离线好友请求
            self.dbEngine.deleteOfflineAddFriendRequestWithUserName(user.DBUser.username)


    #---获取所有离线消息并发送---#
    #---from:handleUserLogin---#
    def getOfflineChatMessageAndSendWithUser(self, user):

        db_offline_chat_messages = self.dbEngine.getAllOfflineChatMessageWithUserName(user.DBUser.username)

        ret_off_chat_messages = []
        if db_offline_chat_messages:
            for off_chat_msg in db_offline_chat_messages:
                fuser = self.dbEngine.getUserInfoWithUserId(off_chat_msg.fromid)
                off_msg = SendToClientPackageChatMessage(fuser.username,
                                                         user.DBUser.username,
                                                         off_chat_msg.groupname,
                                                         off_chat_msg.msg,
                                                         off_chat_msg.last_date)
                ret_off_chat_messages.append(off_msg)

        if ret_off_chat_messages:
            #发送离线消息
            retPackage = SendToClientPackage('sendchatmsg')
            retPackage.status = 1
            retPackage.obj = ret_off_chat_messages

            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

            #从数据库中删除
            self.dbEngine.deleteAllOfflineChatMessageWithUserName(user.DBUser.username)


    #---广播用户的上线下线消息---#
    #---from:handleUserLogin & closeConnection---#
    def broadcastOnlineStatusToAllFriend(self, user, online):

        retPackage = SendToClientPackage('useronoffline')

        for friend in user.getAllFriends():
            #通知所有好友下线
            retPackage.status = 1
            obj = SendToClientUserOnOffStatus(user.DBUser.username,
                                              online)
            retPackage.obj = obj

            if friend.connection:
                friend.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

            if not online:  #离线
                # 清空连接
                online_friend = self.serverList.getUserExistByUsername(friend.DBUser.username)
                if online_friend:
                    # 从好友列表里面将自己的connection 清0
                    myself = online_friend.getFriendWithUsername(user.DBUser.username)
                    myself.connection = None


    #---广播群组成员加退群信息---#
    #---from:handleUserLogin & closeConnection---#
    def broadcastJoinExitStatusToAllMember(self, username, groupname, status):

        retPackage = SendToClientPackage('memberjoinexitgroup')
        group = self.serverList.getGroupByUsername(groupname)
        retPackage.status = 1

        for member in group.members:
            # 0.检查是否在线,在线发送上线通知
            online_friend = self.serverList.getUserExistByUsername(member.DBUser.username)

            # 在线
            if online_friend:
                join_exit_status = SendToClientGroupMemberJoinExitStatus(username,
                                                                         groupname,
                                                                         status)
                retPackage.obj = join_exit_status

                # 发送入退群通知
                online_friend.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))


    #---将在线用户列表里面的所有状态修改为在线---#
    #---from:handleUserLogin---#
    def setUserOnlineInOnlineUsersFriends(self, user):

        for friend in user.getAllFriends():
            online_friend = self.serverList.getUserExistByUsername(friend.DBUser.username)
            if online_friend:
                myself = online_friend.getFriendWithUsername(user.DBUser.username)
                myself.connection = user.connection


    #---获取用户好友列表---#
    #--from:handleGetFriends---#
    def getUserFriendsWithUserAndPage(self, user, page):

        retFriends = []
        friends = user.getAllFriends()
        friendCount = len(friends)
        if friends and friendCount > 0:
            nStart = 0
            nEnd = 0

            #计算页码是否在范围内
            if USERS_PAGES_SIZE * (page - 1) < friendCount:
                nStart = USERS_PAGES_SIZE * (page - 1)
                #计算结束页码
                if USERS_PAGES_SIZE * page > friendCount:
                    nEnd = friendCount - USERS_PAGES_SIZE * page
                else:
                    nEnd = USERS_PAGES_SIZE * page

                #在页码范围内的好友
                friends = friends[nStart: nEnd]
                for friend in friends:
                    online = False
                    if friend.connection:
                        online = True
                    retUser = SendToClientPackageUser(friend.DBUser.username,
                                                      friend.DBUser.sex,
                                                      friend.DBUser.mail,
                                                      online)
                    retFriends.append(retUser)
        return retFriends