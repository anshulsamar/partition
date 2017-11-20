# https://pymotw.com/2/socket/tcp.html
# https://stackoverflow.com/questions/23828264/how-to-make-a-simpl
# e-multithreaded-socket-server-in-python-that-remembers-client
# https://docs.python.org/2/howto/sockets.html#socket-howto

import socket
import sys
from psocket import psocket
from psocket import ERROR
from time import sleep

if (len(sys.argv) < 2):
    print("USAGE: python server.py [node_name]")
    exit()

while True:
    try:
        # connect to master
        print "Attempting to Connect to Master"
        master = psocket(blocking=True)
        master.pconnect('localhost', 10000)
        print "Node <-> Master"

        # start server
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('localhost', 0))
        port = server.getsockname()[1]

        # send port number to master
        msg = "<ID><NODE>" + sys.argv[1] + "<PORT>" + str(port)
        master.psend(msg)

        # get list of node to ports from master
        data = master.precv()
        node_to_port = {}
        for i in data.split(','):
            n = i.split(':')[0]
            p = i.split(':')[1]
            node_to_port[n] = int(p)
        print(node_to_port)
        break
    except:
        sleep(1)
        continue
