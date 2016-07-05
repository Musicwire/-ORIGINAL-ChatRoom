import json

#通用错误
PACKAGE_ERRCODE_USERID          = 10001 #用户ID错误
PACKAGE_ERRCODE_FRIENDID        = 10002 #好友ID错误,此用户不是你好友
PACKAGE_ERRCODE_USERFRIENDID    = 10003 #用户或者好友ID错误,ID非自己ID，或者好友ID与自己ID相同

#注册
PACKAGE_ERRCODE_USERUNEXIST     = 10010 #账号不存在
PACKAGE_ERRCODE_USERISEXIST     = 10011 #帐号存在
PACKAGE_ERRCODE_INPUTWRONG      = 10012 #输入异常
PACKAGE_ERRCODE_LENGTHTOSHORT   = 10013 #帐号或密码长度不足
PACKAGE_ERRCODE_USEDMAIL        = 10014 #邮箱已经使用
PACKAGE_ERRCODE_AUTHFAILED      = 10015 #认证失败

#登录
PACKAGE_ERRCODE_USERNOTEXIST    = 10021 #帐号不存在
PACKAGE_ERRCODE_WRONGPASSWORD   = 10022 #密码错误
PACKAGE_ERRCODE_ANOTHERLOGIN    = 10023 #异地登录，退出当前帐号

#好友
PACKAGE_ERRCODE_FRIENDSHIPEXIST = 10031 #已经是好友
PACKAGE_ERRCODE_NOTHISUSER      = 10032 #不存在此用户

#群组
PACKAGE_ERRCODE_INGROUP         = 10041 #已经在群里
PACKAGE_ERRCODE_NOTINGROUP      = 10042 #不在群里

####################################################################################
# 一.协议解析
####################################################################################
class Protocol(object):

    def __init__(self):
        pass

    @staticmethod
    def checkPackage(package):

        json_msg = json.loads(package)

        protocol = {
            'register':                    PackageRegister,
            'login':                       PackageLogin,
            'addfriend':                   PackageAddFriendRequest,
            'delfriend':                   PackageDeleteFriend,
            'addfriendstatus':             PackageAddFriendStatus,
            'getfriends':                  PackageGetFriends,
            'getfrienddetail':             PackageGetFriendDetail,
            'sendchatmsg':                 PackageSendChatMessage,
            'joingroup':                   PackageJoinGroup,
            'exitgroup':                   PackageExitGroup,
            'registerauth':                PackageRegisterAuth
        }

        if 'datas' in json_msg:
            datas = json_msg['datas']

            if 'type' in datas:
                stype = datas['type']

                #存在协议内
                if stype in protocol.keys():
                    #解析协议
                    pack = protocol[stype]()
                    pack.parser(datas)
                    return pack
        return None

####################################################################################
# 二.接收包协议
####################################################################################

#父包
class Package(object):
    def __init__(self):
        pass

    def parser(self, datas):
        for (k, v) in datas.items():
            try:
                if type(self.__getattribute__(k)) is not None:
                    self.__setattr__(k, v)
            except AttributeError:
                pass

####################################################################################
#注册
class PackageRegister(Package):
    def __init__(self):
        super(PackageRegister, self).__init__()

        self.username = ''
        self.password = ''
        self.sex = 0
        self.mail = ''

#注册认证
class PackageRegisterAuth(Package):
    def __init__(self):
        super(PackageRegisterAuth, self).__init__()

        self.mail = ''
        self.auth = ''

#登录
class PackageLogin(Package):
    def __init__(self):
        super(PackageLogin, self).__init__()

        self.username = ''
        self.password = ''

#申请添加好友
class PackageAddFriendRequest(Package):
    def __init__(self):
        super(PackageAddFriendRequest, self).__init__()

        self.fromname = ''
        self.toname = ''
        self.msg = ''

#同意或者拒绝添加好友申请
class PackageAddFriendStatus(Package):
    def __init__(self):
        super(PackageAddFriendStatus, self).__init__()

        self.fromname=''
        self.toname=''
        self.msg=''
        self.agree = 0

#发送聊天信息
class PackageSendChatMessage(Package):
    def __init__(self):
        super(PackageSendChatMessage, self).__init__()

        self.fromname = ''
        self.toname = ''
        self.groupname = ''
        self.chatmsg = ''

#获取好友列表
class PackageGetFriends(Package):
    def __init__(self):
        super(PackageGetFriends, self).__init__()

        self.username = ''
        self.page = 0

#删除好友
class PackageDeleteFriend(Package):
    def __init__(self):
        super(PackageDeleteFriend, self).__init__()

        self.username = ''
        self.friendname = ''

#获取好友信息
class PackageGetFriendDetail(Package):
    def __init__(self):
        super(PackageGetFriendDetail, self).__init__()

        self.username = ''
        self.friendname = ''

#加入群组
class PackageJoinGroup(Package):
    def __init__(self):
        super(PackageJoinGroup, self).__init__()

        self.groupname = ''
        self.uesrname = ''

#退出群组
class PackageExitGroup(Package):
    def __init__(self):
        super(PackageExitGroup, self).__init__()

        self.groupname = ''
        self.uesrname = ''

####################################################################################
# 三.发送协议
####################################################################################

#父包
class SendToClientPackage(object):
    def __init__(self, action):
        super(SendToClientPackage, self).__init__()

        self.status = 0
        self.errcode = 0

        self.obj = None
        self.action = action

    def reprJSON(self):
        return dict(datas=self.obj,
                    action=self.action,
                    status=self.status,
                    errcode=self.errcode)

class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)

####################################################################################

#注册消息返回
class SendToClientPackageRegister(object):
    def __init__(self):
        pass

#登录情况和好友列表返回
class SendToClientPackageUser(object):
    def __init__(self, username, sex, mail, online=False):

        self.username = username
        self.sex = sex
        self.mail = mail
        self.online = online

    def reprJSON(self):

        return dict(username=self.username,
                    sex=self.sex,
                    mail=self.mail,
                    online=self.online)

#转发好友申请
class SendToClientPackageRecvAddFriendRequest(object):
    def __init__(self, fromname, toname, sex, msg, date):

        self.fromname = fromname
        self.toname = toname
        self.sex = sex
        self.msg = msg
        self.senddate = date

    def reprJSON(self):
        return dict(fromname=self.fromname,
                    toname=self.toname,
                    sex=self.sex,
                    msg=self.msg,
                    senddate=self.senddate.strftime("%Y-%m-%d %H:%M:%S"))

#返回添加好友结果
class SendToClientAddFriendStatus(object):
    def __init__(self, username, toname, sex, msg, agree):

        self.fromname = username
        self.toname = toname
        self.sex = sex
        self.msg = msg
        self.agree = agree

    def reprJSON(self):
        return dict(fromname=self.fromname,
                    toname=self.toname,
                    sex=self.sex,
                    msg=self.msg,
                    agree=self.agree)

#发送消息
class SendToClientPackageChatMessage(object):
    def __init__(self, fromname='', toname='', groupname='', chatmsg='', senddate=''):

        self.fromname = fromname
        self.toname = toname
        self.groupname = groupname
        self.chatmsg = chatmsg
        self.senddate = senddate

    def reprJSON(self):
        return dict(fromname=self.fromname,
                    toname=self.toname,
                    groupname=self.groupname,
                    chatmsg=self.chatmsg,
                    senddate=self.senddate.strftime("%Y-%m-%d %H:%M:%S"))

#好友上线下线消息
class SendToClientUserOnOffStatus(object):
    def __init__(self, username, online):
        self.username = username
        self.online = online

    def reprJSON(self):
        return dict(username=self.username,
                    online=self.online)

#好友进退群消息
class SendToClientGroupMemberJoinExitStatus(object):
    def __init__(self, username, groupname, status):
        self.username = username
        self.groupname = groupname
        self.status = status

    def reprJSON(self):
        return dict(username=self.username,
                    groupname=self.groupname,
                    status=self.status)