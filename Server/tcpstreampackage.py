from protocol import Protocol

class TCPStreamPackage(object):

    def __init__(self, callback):

        super(TCPStreamPackage, self).__init__()

        self.datas = ''
        self._package_decode_callback = callback

    def add(self, data):

        #组包
        if len(self.datas) == 0:
            self.datas = data.decode('utf-8')
            self.bdatas = data

        else:
            self.datas = "%s%s" % (self.datas, data.decode('utf-8'))
            #self.bdatas = b"%s%s" % (self.bdatas, data)

            for x in data:
                self.bdatas += x
        #拆包
        while len(self.datas) != 0:

            length = -1
            length_index = self.datas.find('length\":')

            if length_index != -1:
                length_end = self.datas.find(',', length_index + 8, length_index + 8 + 10)

                if length_end == -1:
                    length_end = self.datas.find('}', length_index + 8, length_index + 8 + 10)

                if length_end != -1:
                    length = self.datas[length_index + 8:length_end]

            if length != -1:
                length = int(length.strip())

            print("length:   ", length)
            print("turelength:   ", len(self.datas))

            if length != -1 and length <= len(self.bdatas):
                package = self.bdatas[0:length].decode('utf-8')

            print("package:   ", package)

            lpackage = len(package)
            package = Protocol.checkPackage(package)

            if self._package_decode_callback:
                self._package_decode_callback(package)

            if len(self.bdatas) == length:
                self.datas = ''
                self.bdatas = b''

            else:
                self.datas = self.datas[lpackage:]
                self.bdatas = self.bdatas[length:]
                print('double package')
                print(self.datas, self.bdatas)