import datetime
import json
import smtplib
import random
from email.mime.text import MIMEText
from OpenSSL.crypto import  FILETYPE_PEM, PKey ,TYPE_RSA, dump_publickey, dump_privatekey
from db import DBEngine, DBUser, DBRelationship, DBOfflineMsg, DBOfflineAddFriend, DBMail
from models import ServeList, GroupObject, UserObject, USERS_PAGES_SIZE
from protocol import PackageLogin, PackageDg, PackagePublicDg, PackageRegister, PackageRegisterAuth, PackageAddFriendRequest, PackageAddFriendStatus , PackageGetFriends , PackageDeleteFriend , PackageGetFriendDetail , PackageSendChatMessage, PackageExitGroup, PackageGetGroupList, PackageGetGroupMember, PackageJoinGroup, PACKAGE_ERRCODE_INPUTWRONG,PACKAGE_ERRCODE_LENGTHTOSHORT,PACKAGE_ERRCODE_USERISEXIST, PACKAGE_ERRCODE_AUTHFAILED, PACKAGE_ERRCODE_LENGTHTOSHORT , PACKAGE_ERRCODE_FRIENDSHIPEXIST , PACKAGE_ERRCODE_USERFRIENDID, PACKAGE_ERRCODE_MAILNOTCONFIRM, PACKAGE_ERRCODE_NOTHISUSER, PACKAGE_ERRCODE_ANOTHERLOGIN, PACKAGE_ERRCODE_USERID, PACKAGE_ERRCODE_USEDMAIL, PACKAGE_ERRCODE_USERUNEXIST, PACKAGE_ERRCODE_INGROUP, PACKAGE_ERRCODE_NOTINGROUP, PACKAGE_ERRCODE_NOTINGROUP, ComplexEncoder, SendToClientPackage, SendToClientPackageUser, SendToClientPackageChatMessage, SendToClientPackageRecvAddFriendRequest, SendToClientAddFriendStatus, SendToClientUserOnOffStatus, SendToClientGroupMemberJoinExitStatus, SendToClientPackageFriendsList, SendToClientPackageAnotherLogin, SendToClientPackageGroupsList, SendToClientPackageGroupsMember, SendToClientPackageDG

#逻辑处理层
class Logic(object):

    #0.初始化
    def __init__(self):
        self.serverList = ServeList()
        self.dbEngine = DBEngine()
        self.groupInit()

    #1.输入是否合法，防止sql注入
    def findBadInput(self, inputstring):

        if '\'' in inputstring:
            return True
        elif '\"' in inputstring:
            return True
        elif '`' in inputstring:
            return True
        elif ' ' in inputstring:
            return True

    #2.初始化群组
    def groupInit(self):
        db_groups = self.dbEngine.get_all_group()
        for db_group in db_groups:
            group = GroupObject(db_group)
            self.serverList.addNewGroup(group)
            self.getGroupMemberWithDB(group)

    #3.重置服务器
    def reset(self):
        self.serverList.reset()

    ####################################################################################
    # 一.协议处理部分
    ####################################################################################

    #0.逻辑处理部分
    def handlePackage(self, connection , package):
        if isinstance(package, PackageRegister):                        #请求邮箱认证码状态返回
            print('package register')
            self.handleUserRegister(connection, package)
        elif isinstance(package, PackageRegisterAuth):                  #注册状态返回
            print('package registerauth')
            self.handleUserRegisterAuth(connection, package)
        elif isinstance(package, PackageLogin):                         #登陆状态返回
            print('package login')
            self.handleUserLogin(connection, package)
        elif isinstance(package, PackageDg):                            #获取DG证书
            print('package dg')
            self.handleDG(connection, package)
        elif isinstance(package, PackagePublicDg):                      #获取DG公钥证书
            print('package publicdg')
            self.handlePublicDg(connection, package)
        elif isinstance(package, PackageAddFriendRequest):              #转发添加好友申请
            print('package addfriend')
            self.handleAddFriendRequest(connection, package)
        elif isinstance(package, PackageAddFriendStatus):               #返回好友添加结果
            print('package addfriendstatus')
            self.handleAddFriendRequestStatus(connection, package)
        elif isinstance(package, PackageDeleteFriend):                  #删除好友通知
            print('package delfriend')
            self.handleDeleteFriend(connection, package)
        elif isinstance(package, PackageGetFriends):                    #好友列表返回
            print('package getfriends')
            self.handleGetFriends(connection, package)
        elif isinstance(package, PackageGetFriendDetail):               #获取好友信息
            print('package getfrienddetail')
            self.handleGetFriendDetail(connection, package)
        elif isinstance(package, PackageJoinGroup):                     #好友加群提醒
            print('package joingroup')
            self.handleJoinGroup(package)
        elif isinstance(package, PackageGetGroupList):                  #获取群列表
            print('package getgrouplist')
            self.handleGetGroupList(connection, package)
        elif isinstance(package, PackageGetGroupMember):                #获取群成员
            print('package getgroupmember')
            self.handleGetGroupMember(connection, package)
        elif isinstance(package, PackageExitGroup):                     #好友退群提醒
            print('package exitgroup')
            self.handleExitGroup(package)
        elif isinstance(package, PackageSendChatMessage):               #发送聊天信息
            print('package sendchatmsg')
            self.handleSendChatMessage(connection, package)

    #1.根据connection断开连接
    def closeConnection(self, connection):
        print("Connection closed")
        user = self.serverList.getUserByConnection(connection)
        if user:
            self.serverList.deleteUserByUser(user)
            friends = user.getAllFriends()
            if len(friends) > 0:
                self.broadcastOnlineStatusToAllFriend(user, 0)

    ####################################################################################
    # 二.逻辑处理
    ####################################################################################


    #----0.请求邮箱认证码状态返回----#
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
                    print('authcode')
                    authcode = self.getauthcode()
                    self.dbEngine.wirte_mail_auth(package.mail, authcode)
                    self.sendmailauth(package.mail, authcode)
                    self.createDGPairs(package.username)
                    #将该验证码存至数据库
                    self.dbEngine.register_new_user(package.username, package.password, package.mail, package.sex)
                    retPackage.status = 1

        connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

    #----1.注册状态返回----#
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

    #----2.登陆状态返回----#
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
                    another.obj = SendToClientPackageAnotherLogin(self.serverList.users[package.username].connection._address[0])

                    online_user.connection.send_message(json.dumps(another, cls=ComplexEncoder))

                    #step 2.关闭联接
                    online_user.connection.close()

                #重新加入到在线用户
                user = UserObject(connection, db_user)
                self.serverList.addNewOnlineUser(user)

                #XMLCertificate = self.createXMLCertificate() 生成XML证书

                retPackage.status = 1
                retPackage.obj = SendToClientPackageUser(user.username,
                                                         user.DBUser.sex,
                                                         user.DBUser.mail)
                #加载好友列表
                print ('getUserFriendsWithDBAndOnLineUsers')
                self.getUserFriendsWithDBAndOnLineUsers(user)

                #广播好友列表，通知本人上线
                print ('broadcastOnlineStatusToAllFriend')
                self.broadcastOnlineStatusToAllFriend(user, 1)

                #修改在线列表,本人上线
                print ('setUserOnlineInOnlineUsersFriends')
                self.setUserOnlineInOnlineUsersFriends(user)

        connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
        if retPackage.status == 1:
            my_user = self.serverList.getUserByConnection(connection)
            #检查离线消息，是否有人希望添加我为好友
            print ('getAllAddFriendRequestFromDBAndSendToClient')
            self.getAllAddFriendRequestFromDBAndSendToClient(my_user)
            #是否有发给我的离线消息
            print ('getOfflineChatMessageAndSendWithUser')
            self.getOfflineChatMessageAndSendWithUser(my_user)
    
    #----3.获取公钥数字证书----#
    def handleDG(self, connection, package):
        user = self.serverList.getUserByConnection(connection)
        retPackage = SendToClientPackage('applymydg')
        #自己的name
        if user.DBUser.username == package.username:
            retPackage.status = 1
            return_obj = SendToClientPackageDG(user.DBUser.username,self.getDGPublicKey(user.DBUser.username))
            retPackage.obj = return_obj
        else:
            retPackage.errcode = PACKAGE_ERRCODE_USERID
        user.connection.send_message(json.dumps(retPackage,cls=ComplexEncoder))

    #----4.获取私钥证书----#
    def handlePublicDg(self, connection, package):
        user = self.serverList.getUserByConnection(connection)
        retPackage = SendToClientPackage('applyfrienddg')
        #自己的name
        if user.DBUser.username == package.username:
            retPackage.status = 1
            return_obj = SendToClientPackageDG(package.friendname,self.getDGPrivateKey(package.friendname))
            retPackage.obj = return_obj
        else:
            retPackage.errcode = PACKAGE_ERRCODE_USERID
        user.connection.send_message(json.dumps(retPackage,cls=ComplexEncoder))

    #----5.转发添加好友申请----#
    def handleAddFriendRequest(self, connection, package):

        user = self.serverList.getUserByConnection(connection)
        retPackage = SendToClientPackage('returnaddfriend')
        bFriendship = False

        #检查是否是自己并且自己不是自己想要添加自己为好友
        if user.DBUser.username == package.fromname and user.DBUser.username != package.toname:
            isexist = self.dbEngine.getUserInfoWithUserName(package.toname)
            #检查用户是否存在
            if isexist:
                friend = user.getFriendWithUsername(package.toname)
                if friend:
                    bFriendship = True

                if not bFriendship:
                    retPackage.status = 1
                    user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

                    #step2 在线,发送添加
                    online_user = self.serverList.getUserExistByUsername(package.toname)

                    if online_user:
                        add_obj = []
                        addreq = SendToClientPackageRecvAddFriendRequest(package.fromname,
                                                                         package.toname,
                                                                         user.DBUser.sex,
                                                                         package.msg,
                                                                         datetime.datetime.now())
                        add_obj.append(addreq)
                        retPackagetofriend = SendToClientPackage('addfriend')
                        retPackagetofriend.status = 1
                        retPackagetofriend.obj = add_obj

                        online_user.connection.send_message(json.dumps(retPackagetofriend, cls=ComplexEncoder))
                    else:
                        #插入数据库,等待上线时候通知
                        print('Insert datebase')
                        self.dbEngine.setOfflineAddFriendReuqest(package.toname, package.fromname, package.msg, datetime.datetime.now())
                else:
                    #已经是好友，返回错误信息
                    retPackage.errcode = PACKAGE_ERRCODE_FRIENDSHIPEXIST
                    user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
            else:
                retPackage.errcode = PACKAGE_ERRCODE_NOTHISUSER
                user.connection.send_message(json.dumps(retPackage,cls=ComplexEncoder))
        else:
            #用户ID错误，或者用户ID等于好友ID
            retPackage.errcode = PACKAGE_ERRCODE_USERFRIENDID
            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

    #----6.返回好友添加结果----#
    def handleAddFriendRequestStatus(self, connection, package):

        user = self.serverList.getUserByConnection(connection)
        retPackage = SendToClientPackage('returnaddfriendstatus')

        #自己的ID是目标ID && 自己不能添加自己为好友
        if user.DBUser.username == package.toname and user.DBUser.username != package.fromname:

            #如果同意
            if package.agree:

                #step 1. 检查是否是自己的好友
                if not self.dbEngine.getFriendshipWithUserFriendName(package.fromname, package.toname):
                    db_friend = self.dbEngine.getUserInfoWithUserName(package.fromname)
                    #在线列表中
                    usob = self.serverList.getUserByUsername(package.fromname)
                    #存在数据库中
                    if db_friend:#判断用户是否存在
                        retPackage.status = 1
                        #保存关系到数据库
                        self.dbEngine.setFriendshipWithUserNames(package.toname, package.fromname)
                        return_obj=[]
                        if usob:#用户在在线列表中

                            return_tem = SendToClientPackageFriendsList(package.fromname,
                                                                        db_friend.sex,
                                                                        db_friend.mail,
                                                                        usob.connection._address[0],
                                                                        package.agree)
                        else:
                            return_tem = SendToClientPackageFriendsList(package.fromname,
                                                                        db_friend.sex,
                                                                        db_friend.mail,
                                                                        '',
                                                                        package.agree)
                        return_obj.append(return_tem)
                        retPackage.obj = return_tem

                        user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
                        #检查是否在线,在线发送上线通知
                        online_friend = self.serverList.getUserExistByUsername(package.fromname)
                        if online_friend:
                            #当前在线
                            retPackagetofriendstatus = SendToClientPackage('addfriendstatus')
                            online_obj = []
                            online_status = SendToClientAddFriendStatus(package.fromname,
                                                                        package.toname,
                                                                        user.DBUser.sex,
                                                                        user.DBUser.mail,
                                                                        user.connection._address[0],
                                                                        package.msg,
                                                                        package.agree,
                                                                        user.online)
                            online_obj.append(online_status)
                            retPackagetofriendstatus.status = 1
                            retPackagetofriendstatus.obj = online_status
                            #发送有人添加好友申请
                            online_friend.connection.send_message(json.dumps(retPackagetofriendstatus, cls=ComplexEncoder))

                            #添加到我的好友列表
                            user.addFriend(online_friend)
                            online_friend.addFriend(user)
                        else:
                            new_friend = UserObject(None,self.dbEngine.getUserInfoWithUserName(package.fromname))
                            user.addfriend(new_friend)
                            #此处应该添加系统回复消息至数据库
                            #用户上线时，将此消息发送

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

    #----7.删除好友通知----#
    def handleDeleteFriend(self, connection, package):

        user = self.serverList.getUserByConnection(connection)
        retPackage = SendToClientPackage('delfriend')

        # 自己的id
        if user.DBUser.username == package.username and user.DBUser.username != package.friendname:
            retPackage.status = 1

            # 从数据库中删除
            self.dbEngine.deleteFriendshipByUserAndFriendName(package.username, package.friendname)

            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

            # 给在线好友发送通知，删除
            online_friend = self.serverList.getUserExistByUsername(package.friendname)
            if online_friend:
                sendObj = SendToClientPackageUser(user.DBUser.username,
                                                  user.DBUser.sex,
                                                  user.DBUser.mail)
                retPackage.obj = sendObj
                online_friend.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
                online_friend.deleteFriend(user)
                # 从维护的好友列表中删除
                user.deleteFriend(online_friend)

        else:
            retPackage.errcode = PACKAGE_ERRCODE_USERID
            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

    #----8.好友列表返回----#
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

    #----9.获得好友信息----#
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

    #----10.加入群组----#
    def handleJoinGroup(self, package):

        user = self.serverList.getUserByUsername(package.username)
        group = self.serverList.getGroupByGroupname(package.groupname)
        retPackage = SendToClientPackage('memberjoinexitgroup')
        if group:#群组已存在
            # step 1. 检查未入群
            if not user.DBUser.username in self.serverList.group[package.groupname].members:
                retPackage.status = 1
                #维护在线列表
                group.addMember(user)
                #保存关系到数据库
                self.dbEngine.add_user_into_group(package.groupname,package.username)
                my_group = self.dbEngine.findGroupidWithGroupname(package.groupname)
                return_obj = SendToClientPackageGroupsList(my_group.groupname,my_group.groupnumber)
                retPackage.obj = return_obj
                user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
                #广播进退群消息(进群)
                self.broadcastJoinExitStatusToAllMember(package.username, package.groupname, True)

            #已经在群里
            else:
                retPackage.errcode = PACKAGE_ERRCODE_INGROUP
                user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
        else:
            retPackage.status = 1
            self.dbEngine.register_new_group(package.groupname)
            self.dbEngine.add_user_into_group(package.groupname,package.username)
            db_gp = self.dbEngine.findGroupidWithGroupname(package.groupname)
            GO_gp = GroupObject(db_gp)
            self.serverList.addNewGroup(GO_gp)
            db_user = self.dbEngine.findIdWithName(package.username)
            GO_user = UserObject(None,db_user)
            GO_gp.addMember(GO_user)
            return_obj = SendToClientPackageGroupsList(package.groupname,1)
            retPackage.obj = return_obj
            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

    #----11.获取群列表----#
    def handleGetGroupList(self, connection, package):
        user = self.serverList.getUserByConnection(connection)
        retPackage = SendToClientPackage('getgrouplist')

        #自己的name
        if user.DBUser.username == package.username:
            return_obj = self.getGroupListWithUser(user)
            if len(return_obj) > 0:
                retPackage.obj =return_obj
            retPackage.status = 1
        else:
            retPackage.errcode = PACKAGE_ERRCODE_USERID
        print ('getgrouplist')
        user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

    #----12.获取群成员----#
    def handleGetGroupMember(self, connection, package):
        user = self.serverList.getUserByConnection(connection)
        group = self.serverList.getGroupByGroupname(package.groupname)
        retPackage = SendToClientPackage('getgroupmember')

        #自己的name
        if user.DBUser.username == package.username:
            #群组是否存在
            if group:
                #用户是群组成员
                if user.DBUser.username in group.members:
                    retPackage.status = 1
                    return_obj = self.getGroupMember(group)
                    if len(return_obj) > 0:
                        retPackage.obj = return_obj
                else:
                    retPackage.errcode = PACKAGE_ERRCODE_NOTINGROUP
            else:
                retPackage.errcode = PACKAGE_ERRCODE_GROUPNOTEXIST
        else:
            retPackage.errcode = PACKAGE_ERRCODE_USERID
        user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

    #----13.退出群组----#
    def handleExitGroup(self, package):

        user = self.serverList.getUserByUsername(package.username)
        group = self.serverList.getGroupByGroupname(package.groupname)
        retPackage = SendToClientPackage('memberjoinexitgroup')
        
        #1群存在
        if group:
            #在群里
            if user.DBUser.username in self.serverList.group[package.groupname].members:
                retPackage.status = 1
                #更新群组成员列表
                group.deleteMember(user)
                #从数据库中删除
                print (package.groupname,package.username)
                self.dbEngine.del_user_from_group(package.groupname,package.username)
                #维护该群的群成员列表
                db_user = self.dbEngine.findIdWithName(package.username)
                GO_user = UserObject(None,db_user)
                group.deleteMember(GO_user)
                #返回退群成功包
                user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
                #获得当前此时群人数
                length = self.dbEngine.get_group_number(package.groupname)
                #群能否继续存在
                if length == 0:
                    #删除该群
                    self.dbEngine.del_the_group(package.groupname)
                    #维护服务器群列表缓存
                    self.serverList.deleteGroupByGroup(group)
                else:
                    #广播进退群消息
                    self.broadcastJoinExitStatusToAllMember(package.username, package.groupname, False)

            #不在群里
            else:
                retPackage.errcode = PACKAGE_ERRCODE_NOTINGROUP
                user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
        else:
            retPackage.errcode = PACKAGE_ERRCODE_NOTINGROUP
            user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))


    #----14.发送聊天消息----#
    def handleSendChatMessage(self, connection, package):

        user = self.serverList.getUserByConnection(connection)
        retPackage = SendToClientPackage('sendchatmsg')

        #不是群组消息
        if package.groupname == '':
            print ("private message")
            #自己的name
            if user.DBUser.username == package.fromname and user.DBUser.username != package.toname:

                #寻找好友
                for friend in user.getAllFriends():

                    if friend.DBUser.username == package.toname:
                        #发送消息给好友
                        retPackage.status = 1

                        user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
                        chat_obj = []
                        chat = SendToClientPackageChatMessage(package.fromname,
                                                              package.toname,
                                                              '',
                                                              package.chatmsg,
                                                              datetime.datetime.now())
                        chat_obj.append(chat)
                        retPackage.obj = chat_obj

                        #在线
                        if friend.connection:
                            friend.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
                        #不在线，数据库插入离线消息
                        else:
                            self.dbEngine.addOfflineChatMessageWithUserName(package.fromname,
                                                                            package.toname,
                                                                            '',
                                                                            package.chatmsg,
                                                                            datetime.datetime.now())
                            print ("insert offlinechatmessage")
                print ('not find friend')
            else:
                retPackage.errcode = PACKAGE_ERRCODE_USERID
                user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

        #是群组消息
        else:
            #判断自己在群内
            if user.DBUser.username in self.serverList.group[package.groupname].members:
                #发送群组消息返回包
                retPackage.status = 1
                user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
                #寻找群内成员
                for member in self.serverList.group[package.groupname].members:
                    #跳过自己
                    if user.DBUser.username == member:
                        continue
                    #构造群组消息
                    chat_obj = []
                    chat = SendToClientPackageChatMessage(package.fromname,
                                                          '',
                                                          package.groupname,
                                                          package.chatmsg,
                                                          datetime.datetime.now())
                    chat_obj.append(chat)
                    retPackage.obj = chat_obj
                    #在线
                    onlineuser = self.serverList.getUserExistByUsername(member)
                    if onlineuser:
                        onlineuser.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))
                    #不在线，数据库插入离线消息
                    else:
                        print ('insert datebase')
                        self.dbEngine.addOfflineChatMessageWithUserName(package.fromname,
                                                                        member,
                                                                        package.groupname,
                                                                        package.chatmsg,
                                                                        datetime.datetime.now())
            else:
                retPackage.errcode = PACKAGE_ERRCODE_NOTINGROUP
                user.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))


    ####################################################################################
    # 三.逻辑中的部分细节处理
    ####################################################################################

    #----1.生成认证码----#
    #----from: 0.handleUserRegister----#
    def getauthcode(self):

        authcode = ''
        for i in range(4):
            authcode += random.choice('abcdefghijklmnopqrstuvwxyz')
        return authcode

    #----2.发送邮箱认证码----#
    #----from: 0.handleUserRegister----#
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

    #----3.生成证书----#
    #----from: 2.handleUserLoginr----#
    def createDGPairs(self,username):

        private_path = 'private/'
        public_path = 'public/'
        private_path += username
        public_path += username
        P = PKey()
        P.generate_key(TYPE_RSA, 1024)
        #写入
        with open(public_path,'w') as f:
            f.write(dump_publickey(FILETYPE_PEM, P).decode('utf-8'))
        with open(private_path,'w') as f:
            f.write(dump_privatekey(FILETYPE_PEM, P).decode('utf-8'))

    #----4.获取私钥----#
    def getDGPrivateKey(self, username):

        path = 'private/'
        path += username
        with open(path,'r',encoding='utf-8') as f:
            PrivateKey = f.read()
        return PrivateKey

    #----5.获取公钥----#
    def getDGPublicKey(self, username):

        path = 'public/'
        path += username
        with open(path,'r',encoding='utf-8') as f:
            PublicKey = f.read()
        return PublicKey

    #----6.获取用户的所有好友信息----#
    #----from: 2.handleUserLogin----#
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

    #---5.获取群组的所有成员信息---#
    #---from: groupInit---#
    def getGroupMemberWithDB(self, group):

        members = self.dbEngine.get_group_member(group.DBGroup.groupname)

        for member in members:
            db_user = self.dbEngine.findNameWithId(member.memberid)
            member = UserObject(None,db_user)
            group.addMember(member)

    #---6.从数据库获取所有离线申请添加好友的用户并发送给用户--#
    #---from: 2.handleUserLogin---#
    def getAllAddFriendRequestFromDBAndSendToClient(self, user):

        add_requests = []
        offline_add_friend_requests = self.dbEngine.getOfflineAddFriendRequests(user.DBUser.username)
        for off_add_req in offline_add_friend_requests:

            fuser = self.dbEngine.getUserInfoWithUserId(off_add_req.fromid)
            send_request = SendToClientPackageRecvAddFriendRequest(fuser.username,
                                                                   user.DBUser.username,
                                                                   user.DBUser.sex,
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


    #---7.获取所有离线消息并发送---#
    #---from: 2.handleUserLogin---#
    def getOfflineChatMessageAndSendWithUser(self, user):

        db_offline_chat_messages = self.dbEngine.getAllOfflineChatMessageWithUserName(user.DBUser.username)

        ret_off_chat_messages = []
        if db_offline_chat_messages:
            for off_chat_msg in db_offline_chat_messages:
                fuser = self.dbEngine.getUserInfoWithUserId(off_chat_msg.fromuserid)
                fgroup = self.dbEngine.getGroupInfoWithGroupId(off_chat_msg.groupid)
                if fgroup.groupname == '':
                    off_msg = SendToClientPackageChatMessage(fuser.username,
                                                            user.DBUser.username,
                                                            fgroup.groupname,
                                                            off_chat_msg.msg,
                                                            off_chat_msg.last_date)
                else:
                    off_msg = SendToClientPackageChatMessage(fuser.username,
                                                            '',
                                                            fgroup.groupname,
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


    # ---8.将在线用户列表里面的所有状态修改为在线---#
    # ---from: 2.handleUserLogin---#
    def setUserOnlineInOnlineUsersFriends(self, user):

        for friend in user.getAllFriends():
            online_friend = self.serverList.getUserExistByUsername(friend.DBUser.username)
            if online_friend:
                myself = online_friend.getFriendWithUsername(user.DBUser.username)
                myself.connection = user.connection


    #---9.广播用户的上线下线消息---#
    #---from: 2.handleUserLogin & closeConnection---#
    def broadcastOnlineStatusToAllFriend(self, user, online):

        retPackage = SendToClientPackage('useronoffline')

        for friend in user.getAllFriends():
            #通知所有好友上下线
            retPackage.status = 1
            if online:
                obj = SendToClientUserOnOffStatus(user.DBUser.username,
                                                  user.connection._address[0],
                                                  online)
            else:
                obj = SendToClientUserOnOffStatus(user.DBUser.username,
                                                  '',
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


    #---10.广播群组成员加退群信息---#
    #---from: 8.handlejoingroup & 9.handleexitgroup---#
    def broadcastJoinExitStatusToAllMember(self, username, groupname, status):

        retPackage = SendToClientPackage('memberjoinexitgroup')
        group = self.serverList.getGroupByGroupname(groupname)
        retPackage.status = 1

        for member in group.members.values():
            #检查是否在线,在线发送上线通知
            online_member = self.serverList.getUserExistByUsername(member.DBUser.username)

            #在线
            if online_member:
                join_exit_status = SendToClientGroupMemberJoinExitStatus(username,
                                                                         groupname,
                                                                         status)
                retPackage.obj = join_exit_status

                #发送入退群通知
                online_member.connection.send_message(json.dumps(retPackage, cls=ComplexEncoder))

    #---11.获取群组列表---#
    def getGroupListWithUser(self, user):
        retList = []
        groups = self.dbEngine.get_list_group(user.DBUser.username)
        if groups:
            for group in groups:
                #根据groupid获取name
                print ("group.groupid",group.groupid)
                my_group = self.dbEngine.getGroupInfoWithGroupId(group.groupid)
                retGroup = SendToClientPackageGroupsList(my_group.groupname,
                                                         my_group.groupnumber)
                retList.append(retGroup)
        return retList
    #---12.获取群组成员
    def getGroupMember(self, group):
        retList = []
        members = group.getAllMember()
        membernum = len(members)
        print ('membernum',membernum)
        if members and membernum > 0:
            for member in members:
                print('username:',member.DBUser.username)
                retGroup = SendToClientPackageGroupsMember(group.DBGroup.groupname,
                	                                       member.DBUser.username)
                retList.append(retGroup)
        return retList
    #---11.获取用户好友列表---#
    #--from: 5.handleGetFriends---#
    def getUserFriendsWithUserAndPage(self, user, page):

        retFriends = []
        friends = user.getAllFriends()
        friendCount = len(friends)
        print ("friendCount",friendCount)
        if friends and friendCount > 0:

            #计算页码是否在范围内
            if USERS_PAGES_SIZE * (page - 1) < friendCount:
                nStart = USERS_PAGES_SIZE * (page - 1)
                #计算结束页码
                if USERS_PAGES_SIZE * page > friendCount:
                    nEnd = friendCount
                else:
                    nEnd = USERS_PAGES_SIZE * page
                print ("nStart",nStart)
                print ("nEnd",nEnd)
                #在页码范围内的好友
                friends = friends[nStart: nEnd]
                for friend in friends:
                    print ("friend.connection:",friend.connection)
                    #在线
                    if friend.connection:
                        retUser = SendToClientPackageFriendsList(friend.DBUser.username,
                                                                 friend.DBUser.sex,
                                                                 friend.DBUser.mail,
                                                                 friend.connection._address[0],
                                                                 True)
                    #不在线
                    else:
                        retUser = SendToClientPackageFriendsList(friend.DBUser.username,
                                                                 friend.DBUser.sex,
                                                                 friend.DBUser.mail,
                                                                 '',
                                                                 False)

                    retFriends.append(retUser)
        return retFriends