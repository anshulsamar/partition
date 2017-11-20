import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', int(sys.argv[1])))

try:
    message = "hello"
    sock.sendall(message)
    reply = ""
    while len(reply) < len(message):
        reply += sock.recv(16)
    print(reply)
finally:
    sock.close()
