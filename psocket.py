# Implementation extended from class mysocket:
# https://docs.python.org/2/howto/sockets.html#socket-howto

import socket
from socket import error
from time import sleep

ERROR = 0

class psocket:

    def __init__(self, sock=None, blocking=True):
        if sock is None:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock
        if blocking == False:
            self.sock.setblocking(0)

    def pconnect(self, host, port):
        self.sock.connect((host, port))

    def psend(self, data):
        data += "<EOM>"
        self.sock.sendall(data)
        
    def precv(self):
        data = ""
        while True:           
            chunk = self.sock.recv(16)
            if chunk == '':
                raise RuntimeError("Connection Broken")
            else:
                data += chunk
            if data[-5:] == "<EOM>":
                return data[0:-5]
