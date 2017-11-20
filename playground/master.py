import socket
import sys
from psocket import psocket
import threading
from psocket import ERROR

node_to_port = {'master':10000}

# socket to accept connections from new workers
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('localhost', 10000))
print("Master Started on Port 10000")
server.listen(5)

while True:
    try:
        sock, client_address = server.accept()
        print("Master <-> Node: " + str(client_address))
        sock = psocket(sock, blocking = True)
        #sleep(5)
        data = sock.precv()   
        if data[0:4] == "<ID>":
            ind1 = data.find("<NODE>")
            ind2 = data.find("<PORT>")
            node_to_port[data[ind1+6:ind2]] = int(data[ind2+6:])
            config = ""
            for i,v in node_to_port.iteritems():
                config += str(i) + ":" + str(v) + ","
            sock.psend(config[0:-1])
    except: continue
        
