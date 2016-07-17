from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
from tornado.ioloop import IOLoop

from tcpstreampackage import TCPStreamPackage
from logic import Logic
import time
######################################################################
class Connection(object):

    logic = Logic()

    def __init__(self, stream, address):
        self._stream = stream
        self._address = address
        self._stream.set_close_callback(self.on_close)
        self._stream_package = TCPStreamPackage(self.onPackageDecode)
        self.read_message()

        print("A new user has entered the chat room.", address)

    ######################################################################
    def read_message(self):
        self._stream.read_until_close(self.broadcast_message, self.broadcast_streaming_message)

    def broadcast_message(self, data):
        pass

    def broadcast_streaming_message(self, data):
        #data = data.decode('utf-8')
        print('rev:  ', data)
        self._stream_package.add(data)

    def send_message(self, data):
        data2 = data.encode('utf-8')
        print(b'send:   ', data2)
        try:
            time.sleep(0.1)
            self._stream.write(data2)
        except StreamClosedError as err:
            print("%s error:\n%r\ndata: %s" % (self._address, err, data))

    def close(self):
        self._stream.close()

    def on_close(self):
        print("A user has left the chat room.", self._address)
        Connection.logic.closeConnection(self)

    ######################################################################
    def onPackageDecode(self, package):
        Connection.logic.handlePackage(self, package)

######################################################################
#
######################################################################

class ChatServer(TCPServer):

    def handle_stream(self, stream, address):
        print("New connection :", address, stream)
        Connection(stream, address)

if __name__ == '__main__':

    print("Server start ......")
    server = ChatServer()
    server.listen(8000)
    IOLoop.instance().start()