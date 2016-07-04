USERS_PAGES_SIZE = 20

class UserObject(object):

    def __init__(self, connection, dbuser):
        #关键字用用户唯一的用户名
        self.friends = {}
        self.connection = connection
        self.DBUser = dbuser
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
        return self.friends.values()

    def getFriendWithUsername(self , username):
        #根据用户名获取好友
        if username in self.friends:
            return self.friends[username]
        else:
            return None

    def getFriendWithId(self, friendId):
        #根据用户ID获取好友
        for friend in self.friends.values():
            if friend.DBUser.uid == friendId:
                return friend
        return None


class UserModel(object):

    def __init__(self):
        #关键字用用户唯一的用户名
        self.users = {}

    def addNewOnlineUser(self, user):
        #新增用户
        self.users[user.DBUser.username] = user

    def deleteUserBecauseOffline(self, user):
        #用户下线以后，从在线中删除
        del self.users[user.DBUser.username]

    def getUserByConnection(self, connection):
        #根据连接获取用户信息
        for user in self.users.values():
            if user.connection == connection:
                return user
        return None

    def getUserExistByUserid(self, userid):
        #根据用户id判断用户是否在线,并返回
        for user in self.users.values():
            if user.DBUser.uid == userid:
                return user
        return None

    def getUserExistByUsername(self, username):
        #根据用户名称判断用户是否在线,并返回，确保用户登录的唯一
        if username in self.users:
            return self.users[username]
        return None

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

    def reset(self):
        #服务器重置
        del self.users
        self.users = {}