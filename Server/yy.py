from OpenSSL.crypto import load_privatekey, FILETYPE_PEM, PKey ,TYPE_RSA, dump_publickey, dump_privatekey
import base64
   
def createDGPairs(username):
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

def getDGPrivateKey(username):
    path = 'private/'
    path +=username
    with open(path,'r',encoding='utf-8') as f:
        PrivateKey = f.read()
    return PrivateKey
if __name__ == '__main__':
	createDGPairs('willin')