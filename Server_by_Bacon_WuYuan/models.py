USERS_PAGES_SIZE = 20

class ServeList(object):

    def __init__(self):
        #关键字用用户唯一的用户名
        self.users = {}
        self.group = {}

    def addNewOnlineUser(self, user):
        #新增用户
        self.users[user.DBUser.username] = user

    def deleteUserByUser(self, user):
        #根据好友，从用户列表中删除
        if user.DBUser.username in self.users:
            del self.users[user.DBUser.username]

    def deleteUserByConnection(self, connection):
        #根据connection删除好友
        for user in self.users.values():
            if user.connection == connection:
                self.deleteUserByUser(user)
                break

    def getUserByConnection(self, connection):
        #根据连接获取用户信息
        for user in self.users.values():
            if user.connection == connection:
                return user
        return None

    def getUserByUsername(self, username):
        #根据用户名获取用户信息
        for user in self.users.values():
            if user.DBUser.username == username:
                return user
        return None

    def getUserExistByUsername(self, username):
        #根据用户名称判断用户是否在线,并返回，确保用户登录的唯一
        if username in self.users:
            return self.users[username]
        return None

    def addNewGroup(self, group):
        #新增群组
        self.group[group.DBGroup.groupname] = group

    def deleteGroupByGroup(self, group):
        #根据群名删除群组
        if group.DBGroup.groupname in self.group:
            del self.group[group.DBGroup.groupname]

    def getGroupByGroupname(self, groupname):
        #根据群组名获取群组信息
        for group in self.group:
            if group.DBGroup.groupname == groupname:
                return group
        return None

    def reset(self):
        #服务器重置
        del self.users
        self.users = {}

class GroupObject(object):

    def __init__(self, dbgroup):
        self.DBGroup = dbgroup
        self.members = {}

    def addMember(self, user):
        #添加群组成员
        self.members[user.DBUser.username] = user

    def deleteMember(self, user):
        #删除群组
        if user.DBUser.username in self.members:
            del self.members[user.DBUser.username]

    def getAllMember(self):
        #获取成员列表
        return list(self.members.values())

    def getMemberWithUsername(self, username):
        #根据用户名获取成员
        if username in self.members:
            return self.members[username]
        else:
            return None

class UserObject(object):

    def __init__(self, connection, dbuser):
        #关键字为用户唯一的用户名
        self.DBUser = dbuser
        self.friends = {}
        self.connection = connection
        #是否在线
        self.online = False

    def addFriend(self, user):
        #添加好友
        self.friends[user.DBUser.username] = user

    def deleteFriend(self, user):
        #删除好友
        if user.DBUser.username in self.friends:
            del self.friends[user.DBUser.username]

    def getAllFriends(self):
        #获取好友列表
        return list(self.friends.values())

    def getFriendWithUsername(self, username):
        #根据用户名获取好友
        if username in self.friends:
            return self.friends[username]
        else:
            return None