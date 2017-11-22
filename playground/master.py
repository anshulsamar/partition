import socket
import sys
from psocket import psocket
import threading
from psocket import ERROR

def serialize_dict (d):
    config = ""
    for i,v in d.iteritems():
        config += str(i) + ":" + str(v) + ","
    return config[0:-1]

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
            key = data[ind1+6:ind2]
            val = data[ind2+6:]
            node_to_port[data[ind1+6:ind2]] = int(data[ind2+6:])
            sock.psend(serialize_dict(node_to_port))
    except: continue
        
