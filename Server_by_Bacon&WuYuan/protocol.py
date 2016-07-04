import json
import types

#通用错误
PACKAGE_ERRCODE_USERID          = 10001
PACKAGE_ERRCODE_FRIENDID        = 10002
PACKAGE_ERRCODE_USERFRIENDID    = 10003

#注册
PACKAGE_ERRCODE_USERUNEXIST     = 10010
PACKAGE_ERRCODE_USERISEXIST     = 10011
PACKAGE_ERRCODE_INPUTWRONG      = 10012
PACKAGE_ERRCODE_LENGTHTOSHORT   = 10013


#登录
PACKAGE_ERRCODE_USERNOTEXIST    = 10021
PACKAGE_ERRCODE_WRONGPASSWORD   = 10022
PACKAGE_ERRCODE_ANOTHERLOGIN    = 10023

#好友
PACKAGE_ERRCODE_FRIENDSHIPEXIST = 10031
PACKAGE_ERRCODE_NOTHISUSER      = 10032

####################################################################################
#接收包协议
####################################################################################
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

        self.username = ''
        self.friendname = ''
        self.msg = ''

#同意或者拒绝添加好友申请
class PackageAddFriendStatus(Package):
    def __init__(self):
        super(PackageAddFriendStatus, self).__init__()

        self.username=''
        self.friendname=''
        self.msg=''
        self.agree = 0

#发送聊天信息
class PackageSendChatMessage(Package):
    def __init__(self):
        super(PackageSendChatMessage, self).__init__()

        self.username = 0
        self.friendname = 0
        self.chatmsg = ''

#获取好友列表
class PackageGetFriends(Package):
    def __init__(self):
        super(PackageGetFriends, self).__init__()

        self.username = 0
        self.page = 0

#删除好友
class PackageDeleteFriend(Package):
    def __init__(self):
        super(PackageDeleteFriend, self).__init__()

        self.username = 0
        self.friendname = 0

#获取好友信息
class PackageGetFriendDetail(Package):
    def __init__(self):
        super(PackageGetFriendDetail, self).__init__()

        self.username = 0
        self.friendname = 0

####################################################################################
#发送协议
####################################################################################
class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)


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

####################################################################################

class SendToClientPackageRegister(object):
    #注册消息返回
    def __init__(self):
        pass


class SendToClientPackageUser(object):
    #登录情况和好友列表返回
    def __init__(self, username, sex, online=False):

        self.username = username
        self.sex = sex
        self.online = online

    def reprJSON(self):

        return dict(
            username=self.username,
            sex=self.sex,
            online=self.online)


class SendToClientPackageRecvAddFriendRequest(object):
    #转发好友申请
    def __init__(self, fromname, toname, sex, msg, date):

        self.fromname = fromname
        self.toname = toname
        self.sex = sex
        self.msg = msg
        self.senddate = date

    def reprJSON(self):
        return dict(
            fromname=self.fromname,
            toname=self.toname,
            sex=self.sex,
            msg=self.msg,
            senddate=self.senddate.strftime("%Y-%m-%d %H:%M:%S"))


class SendToClientAddFriendStatus(object):
    #返回添加好友结果
    def __init__(self, username, toname, sex, msg, agree):

        self.fromname = username
        self.toname = toname
        self.sex = sex
        self.msg = msg
        self.agree = agree

    def reprJSON(self):
        return dict(
            fromname=self.fromname,
            toname=self.toname,
            sex=self.sex,
            msg=self.msg,
            agree=self.agree)


class SendToClientPackageChatMessage(object):
    #发送消息
    def __init__(self, fromname='', toname='', chatmsg=''):

        self.fromname = fromname
        self.toname = toname
        self.chatmsg = chatmsg

    def reprJSON(self):
        return dict(fromname=self.fromname,
                    toname=self.toname,
                    chatmsg=self.chatmsg)

class SendToClientPackageOfflineChatMessage(object):
    #发送离线消息
    def __init__(self, fromname, toname, msg, senddate):

        self.fromname = fromname
        self.toname = toname
        self.chatmsg = msg
        self.senddate = senddate

    def reprJSON(self):
        return dict(
            fromname=self.fromname,
            toname=self.toname,
            chatmsg=self.chatmsg,
            senddate=self.senddate.strftime("%Y-%m-%d %H:%M:%S"))


class SendToClientUserOnOffStatus(object):
    #好友上线下线消息
    def __init__(self, username, online):
        self.username = username
        self.online = online

    def reprJSON(self):
        return dict(
            username=self.username,
            online=self.online)

####################################################################################
#协议解析
####################################################################################
class Protocol(object):

    def __init__(self):
        pass

    @staticmethod
    def checkPackage(package):

        json_msg = json.loads(package)

        protocol = {
                'login':                       PackageLogin,
                'addfriend':                   PackageAddFriendRequest,
                'addfriendstatus':             PackageAddFriendStatus,
                'getfriends':                  PackageGetFriends,
                'delfriend':                   PackageDeleteFriend,
                'getfrienddetail':             PackageGetFriendDetail,
                'sendchatmsg':                 PackageSendChatMessage,
                'register':                    PackageRegister,
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