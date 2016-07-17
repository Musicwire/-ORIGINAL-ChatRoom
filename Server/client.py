import socket
import time


class client(object):
	"""
	docstring for client
	"""
	def __init__(self):
		self.HOST, self.PORT = "127.0.0.1", int(8000)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.HOST, self.PORT))
	def register(self, username, password, sex, mail):
		pass
	def login(self, username):
		sendbuf1 = b"{\"length\":80,\"datas\":{\"type\":\"login\",\"username\":\"willin\",\"password\":1803883025}}"
		sendbuf2 = b"{\"length\":81,\"datas\":{\"type\":\"login\",\"username\":\"caonima2\",\"password\":124168198}}"
		if username == 'caonima1':
			self.sock.send(sendbuf1)
			print ('send:   ',sendbuf1)
		elif username == 'caonima2':
			self.sock.send(sendbuf2)
			print ('send:   ',sendbuf2)
		time.sleep(0.1)
		response =self.sock.recv(1024)
		print ('recv:   ',response)
		self.sock.send(b"{\"length\":72,\"datas\":{\"type\":\"getfriends\",\"username\":\"willin\",\"page\":1}}")
		#self.sock.send(b"{\"length\":105,\"datas\":{\"type\":\"addfriend\",\"fromname\":\"caonima1\",\"toname\":\"caonima2\",\"msg\":\"I like you!\"}}")
		#sendBufaddfriendstatus = b'{\"length\":125,\"datas\":{\"type\":\"addfriendstatus\",\"fromname\":\"caonima1\",\"toname\":\"caonima2\",\"msg\":\"i love you,too!\",\"agree\":1}}'
		#self.sock.send(sendBufaddfriendstatus)
		time.sleep(0.1)
		response =self.sock.recv(1024)
		print ('recv:   ',response)
		time.sleep(0.1)
		response =self.sock.recv(1024)
		print ('recv:   ',response)
		response =self.sock.recv(1024)
		print ('recv:   ',response)




# [sleep() before recv() is necessary]
#time.sleep(0.1)

#register
#sendBufRegister = b"{\"length\":119,\"datas\":{\"type\":\"register\",\"username\":\"nima2345\",\"password\":895640624,\"sex\":0,\"mail\":\"751300962@qq.com\"}}"
#print (len(sendBufRegister))
#print (sendBufRegister)
#sock.send(sendBufRegister)
#response = sock.recv(1024)
#print (response.decode('utf-8'))
#login
#sendBufLogin = 
#print (sendBufLogin)
#print (len(sendBufLogin))
#sock.send(sendBufLogin)
#response = sock.recv(1024)
#print (response)
#addfriend
#sendBufAddfriend = b"{\"length\":79,\"datas\":{\"type\":\"addfriend\",\"uid\":1,\"fid\":10,\"msg\":\"I like you!\"}}"
#print (sendBufAddfriend)
#sock.send(sendBufAddfriend)
#response = sock.recv(1024)
#print (response)
#while 1:
#	response = sock.recv(1024)
#	print (response)
#time.sleep(5)
# Close the Socket
#sock.close()

#time.sleep(1)
if __name__ == '__main__':
	my_client = client()
	tem = input()		
	if tem == 'login caonima1':
		my_client.login('caonima1')
	else:
		my_client.login('caonima2')
	#sendBufAddfriend = b"{\"length\":105,\"datas\":{\"type\":\"addfriend\",\"fromname\":\"caonima1\",\"toname\":\"caonima2\",\"msg\":\"I like you!\"}}"
	#print (len(sendBufAddfriend))