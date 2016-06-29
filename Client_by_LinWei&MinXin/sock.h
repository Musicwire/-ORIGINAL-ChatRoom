#ifndef SOCKET_H
#define SOCKET_H

#include <WinSock2.h>

#include <string>

/*
 几个关键函数的说明
 SocketClient  为创建一个客户端的socket类,使用如下：SocketClient s("220.181.111.188", 80);
 发送数据调用函数示例：s.SendLine("GET / HTTP/1.1\n");必须有一个换行符或者空字符标识结束
 
 服务端使用方法：
 SocketServer in(2000,5);//第一个参数是端口号，第2个参数是允许最大的连接主机数
 
 while (1)
 {
 Socket* s=in.Accept();
 string r=s->ReceiveLine();
 }
*/


enum TypeSocket {BlockingSocket, NonBlockingSocket};

class Socket {
public:
    
    virtual ~Socket();
    Socket(const Socket&);
    Socket& operator=(Socket&);
    
    std::string ReceiveLine();
    std::string ReceiveBytes();
    
    void   Close();
    
    // The parameter of SendLine is not a const reference
    // because SendLine modifes the std::string passed.
    void   SendLine (std::string);
    
    // The parameter of SendBytes is a const reference
    // because SendBytes does not modify the std::string passed
    // (in contrast to SendLine).
    void   SendBytes(const std::string&);
    
protected:
    friend class SocketServer;
    friend class SocketSelect;
    
    Socket(SOCKET s);
    Socket();
    
    
    SOCKET s_;
    
    int* refCounter_;
    
private:
    static void Start();
    static void End();
    static int  nofSockets_;
};

class SocketClient : public Socket {
public:
    SocketClient(const std::string& host, int port);
};

class SocketServer : public Socket {
public:
    SocketServer(int port, int connections, TypeSocket type=BlockingSocket);
    
    Socket* Accept();
};

class SocketSelect {
public:
    SocketSelect(Socket const * const s1, Socket const * const s2=NULL, TypeSocket type=BlockingSocket);
    
    bool Readable(Socket const * const s);
    
private:
    fd_set fds_;
}; 



#endif