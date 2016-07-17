import json

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
            'register':                    PackageRegister,             #注册请求邮箱认证码
            'registerauth':                PackageRegisterAuth,         #发送注册认证码完成注册
            'login':                       PackageLogin,                #登陆
            'applymydg':                   PackageDg,                   #数字证书
            'applyfrienddg':               PackagePublicDg,             #公钥证书
            'addfriend':                   PackageAddFriendRequest,     #添加好友
            'addfriendstatus':             PackageAddFriendStatus,      #是否同意添加
            'delfriend':                   PackageDeleteFriend,         #删除好友
            'getfriends':                  PackageGetFriends,           #获取好友列表
            'getfrienddetail':             PackageGetFriendDetail,      #获取好友信息
            'sendchatmsg':                 PackageSendChatMessage,      #发送信息
            'joingroup':                   PackageJoinGroup,            #加入群组
            'getgrouplist':                PackageGetGroupList,         #获取群列表
            'getgroupmember':              PackageGetGroupMember,       #获取群成员
            'exitgroup':                   PackageExitGroup             #退出群组
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

#0.父包
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

#1.注册请求邮箱认证码
class PackageRegister(Package):
    def __init__(self):
        super(PackageRegister, self).__init__()

        self.username = ''
        self.password = 0
        self.sex = 0
        self.mail = ''

#2.发送注册认证码完成注册
class PackageRegisterAuth(Package):
    def __init__(self):
        super(PackageRegisterAuth, self).__init__()

        self.mail = ''
        self.auth = ''

#3.登录
class PackageLogin(Package):
    def __init__(self):
        super(PackageLogin, self).__init__()

        self.username = ''
        self.password = 0
#数字证书
class PackageDg(Package):
    def __init__(self):
        super(PackageDg, self).__init__()

        self.username = ''
#获取数字证书公钥
class PackagePublicDg(Package):
    def __init__(self):
        super(PackagePublicDg, self).__init__()

        self.username = ''
        self.friendname = ''

#4.申请添加好友
class PackageAddFriendRequest(Package):
    def __init__(self):
        super(PackageAddFriendRequest, self).__init__()

        self.fromname = ''
        self.toname = ''
        self.msg = ''

#5.同意或者拒绝添加好友申请
class PackageAddFriendStatus(Package):
    def __init__(self):
        super(PackageAddFriendStatus, self).__init__()

        self.fromname=''
        self.toname=''
        self.msg=''
        self.agree = 0

#6.发送聊天信息
class PackageSendChatMessage(Package):
    def __init__(self):
        super(PackageSendChatMessage, self).__init__()

        self.fromname = ''
        self.toname = ''
        self.groupname = ''
        self.chatmsg = ''

#7.获取好友列表
class PackageGetFriends(Package):
    def __init__(self):
        super(PackageGetFriends, self).__init__()

        self.username = ''
        self.page = 0

#8.获取好友信息
class PackageGetFriendDetail(Package):
    def __init__(self):
        super(PackageGetFriendDetail, self).__init__()

        self.username = ''
        self.friendname = ''

#9.删除好友
class PackageDeleteFriend(Package):
    def __init__(self):
        super(PackageDeleteFriend, self).__init__()

        self.username = ''
        self.friendname = ''

#10.加入群组
class PackageJoinGroup(Package):
    def __init__(self):
        super(PackageJoinGroup, self).__init__()

        self.groupname = ''
        self.username = ''

#11.获得群组列表
class PackageGetGroupList(Package):
    def __init__(self):
        super(PackageGetGroupList, self).__init__()

        self.username = ''

#12.获得群组成员
class PackageGetGroupMember(Package):
    def __init__(self):
        super(PackageGetGroupMember, self).__init__()
        self.username = ''
        self.groupname = ''

#13.退出群组
class PackageExitGroup(Package):
    def __init__(self):
        super(PackageExitGroup, self).__init__()

        self.groupname = ''
        self.username = ''

####################################################################################
# 三.发送协议
####################################################################################

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
PACKAGE_ERRCODE_MAILNOTCONFIRM  = 10024 #邮箱没有被注册

#好友
PACKAGE_ERRCODE_FRIENDSHIPEXIST = 10031 #已经是好友
PACKAGE_ERRCODE_NOTHISUSER      = 10032 #不存在此用户

#群组
PACKAGE_ERRCODE_INGROUP         = 10041 #已经在群里
PACKAGE_ERRCODE_NOTINGROUP      = 10042 #不在群里
PACKAGE_ERRCODE_GROUPNOTEXIST   = 10043 #群组不存在

#0.父包
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

#1.登录状态返回,删除好友通知
class SendToClientPackageUser(object):
    def __init__(self, username, sex, mail):

        self.username = username
        self.sex = sex
        self.mail = mail

    def reprJSON(self):
        return dict(username=self.username,
                    sex=self.sex,
                    mail=self.mail)

#2.异地登陆
class SendToClientPackageAnotherLogin(object):
    def __init__(self, ipaddress):

        self.ipaddress = ipaddress

    def reprJSON(self):
        return dict(address=self.ipaddress)

#3.转发好友申请
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

#4.返回添加好友结果
class SendToClientAddFriendStatus(object):
    def __init__(self, username, toname, sex, mail, ipaddress, msg, agree, online=False):

        self.fromname = username
        self.toname = toname
        self.sex = sex
        self.mail = mail
        self.ipaddress = ipaddress
        self.msg = msg
        self.agree = agree
        self.online = online

    def reprJSON(self):
        return dict(fromname=self.fromname,
                    toname=self.toname,
                    sex=self.sex,
                    mail=self.mail,
                    ipaddress=self.ipaddress,
                    msg=self.msg,
                    agree=self.agree,
                    online=self.online)
#证书
class SendToClientPackageDG(object):
    def __init__(self, username, key):

        self.username = username
        self.key = key

    def reprJSON(self):
        return dict(username=self.username,
                    key=self.key)
#5.好友列表返回
class SendToClientPackageFriendsList(object):
    def __init__(self, username, sex, mail, ipaddress, online=False):

        self.username = username
        self.sex = sex
        self.mail = mail
        self.ipaddress = ipaddress
        self.online = online

    def reprJSON(self):
        return dict(username=self.username,
                    sex=self.sex,
                    mail=self.mail,
                    ipaddress=self.ipaddress,
                    online=self.online)

#6.发送消息
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

#7.好友上线下线消息
class SendToClientUserOnOffStatus(object):
    def __init__(self, username, ipaddress, online):

        self.username = username
        self.ipaddress = ipaddress
        self.online = online

    def reprJSON(self):
        return dict(username=self.username,
                    ipaddress=self.ipaddress,
                    online=self.online)

#8.群成员好友获取
class SendToClientPackageGroupsMember(object):
    def __init__(self, groupname, username):
        self.groupname = groupname
        self.username = username
    def reprJSON(self):
        return dict(groupname=self.groupname,
                    username=self.username)

#9.群列表返回消息&&好友加群成功返回消息
class SendToClientPackageGroupsList(object):
    def __init__(self, groupname, groupnumber):
        self.groupname = groupname
        self.groupnumber = groupnumber
    def reprJSON(self):
        return dict(groupname=self.groupname,
                    groupnumber=self.groupnumber)

#10.好友进退群消息
class SendToClientGroupMemberJoinExitStatus(object):
    def __init__(self, username, groupname, status):

        self.username = username
        self.groupname = groupname
        self.status = status

    def reprJSON(self):
        return dict(username=self.username,
                    groupname=self.groupname,
                    status=self.status)