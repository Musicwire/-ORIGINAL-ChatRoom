USERS_PAGES_SIZE = 20

####################################################################################
# 一.开服期间用户及群组状态列表
####################################################################################
class ServeList(object):

    #0.初始化
    def __init__(self):

        self.users = {}
        self.group = {}

    #1.新增用户
    def addNewOnlineUser(self, user):

        self.users[user.DBUser.username] = user

    #2.根据好友，从用户列表中删除
    def deleteUserByUser(self, user):

        if user.DBUser.username in self.users:
            del self.users[user.DBUser.username]

    #3.根据connection删除好友
    def deleteUserByConnection(self, connection):

        for user in self.users.values():
            if user.connection == connection:
                self.deleteUserByUser(user)
                break

    #4.根据连接获取用户信息
    def getUserByConnection(self, connection):

        for user in self.users.values():
            if user.connection == connection:
                return user
        return None

    #5.根据用户名获取用户信息
    def getUserByUsername(self, username):

        for user in self.users.values():
            if user.DBUser.username == username:
                return user
        return None

    #6.根据用户名称判断用户是否在线,并返回，确保用户登录的唯一
    def getUserExistByUsername(self, username):

        if username in self.users:
            return self.users[username]
        return None

    #7.新增群组
    def addNewGroup(self, group):

        self.group[group.DBGroup.groupname] = group

    #8.根据群名删除群组
    def deleteGroupByGroup(self, group):

        if group.DBGroup.groupname in self.group:
            del self.group[group.DBGroup.groupname]

    #9.根据群组名获取群组信息
    def getGroupByGroupname(self, groupname):

        for gp in self.group.values():
            if gp.DBGroup.groupname == groupname:
                return gp
        return None

    #10.服务器重置
    def reset(self):

        del self.users
        self.users = {}

####################################################################################
# 二.群组对象
####################################################################################
class GroupObject(object):

    #0.初始化
    def __init__(self, dbgroup):
        self.DBGroup = dbgroup
        self.members = {}

    #1.添加群组成员
    def addMember(self, user):
        self.members[user.DBUser.username] = user

    #2.删除群组成员
    def deleteMember(self, user):

        if user.DBUser.username in self.members:
            del self.members[user.DBUser.username]

    #3.获取成员列表
    def getAllMember(self):

        return list(self.members.values())

    #4.根据用户名获取成员
    def getMemberWithUsername(self, username):
        if username in self.members:
            return self.members[username]
        else:
            return None

####################################################################################
# 三.用户对象
####################################################################################
class UserObject(object):

    #0.初始化
    def __init__(self, connection, dbuser):

        self.DBUser = dbuser
        self.friends = {}
        self.connection = connection
        self.online = False

    #1.添加好友
    def addFriend(self, user):

        self.friends[user.DBUser.username] = user

    #2.删除好友
    def deleteFriend(self, user):

        if user.DBUser.username in self.friends:
            del self.friends[user.DBUser.username]

    #3.获取好友列表
    def getAllFriends(self):

        return list(self.friends.values())

    #4.根据用户名获取好友
    def getFriendWithUsername(self, username):

        if username in self.friends:
            return self.friends[username]
        else:
            return None