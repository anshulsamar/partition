# Basic threading/networking code taken from folowing tutorial:
# https://pymotw.com/2/socket/tcp.html
# https://stackoverflow.com/questions/23828264/how-to-make-a-simpl
# e-multithreaded-socket-server-in-python-that-remembers-client
# https://docs.python.org/2/howto/sockets.html#socket-howto
# https://pymotw.com/2/threading/

import socket
import sys
from psocket import psocket
from graphviz import Graph
from time import sleep
import pickle
import threading
import os

def server():
    # start server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', my_port))
    port = server.getsockname()[1]
    server.listen(5)
    while True:
        try:
            sock, client_address = server.accept()
            print("Accepted connection from: " + str(client_address))
            sock = psocket(sock, blocking = True)
            data = sock.precv()
            print(data)
            sock.psend(data)
            sock.close()
        except: continue

def client():
    while True:
        for node in nodes:
            if node == my_node: continue
            try:
                # connects to node
                print "Client: Attempting --> Node: " + str(node)
                sock = psocket(blocking = True)
                sock.pconnect('localhost', node_to_port[node])
                print "Client: Connected!"
            
                # send port number to master
                msg = "Client Send: Hello from Node: " + str(my_node)
                sock.psend(msg)
            
                # get list of node to ports from master
                data = sock.precv()
                sock.close()
                print("Client Recv: " + data)
                break
            except:
                sleep(1)
                continue

def redo_log():
    if not os.path.isfile(direct + 'log.txt'): return

# Prints graph and nodes (only the view this node has)
# Not tested
def print_graph (fname):
    g = Graph('G', filename=fname, format='png')
    c = {}
    print(nodes)
    for node in nodes:
        # Note 'cluster_' prefix required naming
        node_name = 'cluster_' + str(node)        
        c[node] = Graph(name=node_name)
        c[node].attr(style='filled')
        c[node].attr(color='lightgrey')
        c[node].node_attr.update(style='filled', color='white')
        for v, n in v_to_node.iteritems():
            if n == node:
                c[node].node(str(v))
        c[node].attr(fontsize='8')
        c[node].attr(label=node_name)
        g.subgraph(c[node])

    edges_added = set()
    for v in v_to_v:
        for vi in v_to_v[v]:
            if (v,vi) not in edges_added:
                g.edge(str(v),str(vi))
                edges_added.add((v,vi))
                edges_added.add((vi,v))
    g.render(fname)

def print_data_structures():
    print "Vertex Set:"
    print(v_set)
    print "Vertex to Node"
    print(v_to_node)
    
if (len(sys.argv) < 2):
    print("USAGE: python node.py [node_id]")
    exit()

my_node = int(sys.argv[1])
direct = "node_" + str(my_node) + "/"
config = pickle.load(open(direct + 'config.p','rb'))
capacity = config[0]
my_port = config[1]
nodes = config[2]

# data structures for graph
v_set = pickle.load(open(direct + 'v_set.p','rb'))
v_to_v = pickle.load(open(direct + 'v_to_v.p','rb'))
v_to_node = pickle.load(open(direct + 'v_to_node.p','rb'))
print_data_structures()

# keep track of other node/ports
node_to_port = pickle.load(open(direct + 'node_to_port.p','rb'))

# catch node up to speed
redo_log ()
print_graph(direct + str(my_node))

# start client threads
print "Starting Server"
server_t = threading.Thread(target=server)
server_t.daemon = True
server_t.start()
print "Starting Client"
client_t = threading.Thread(target=client)
client_t.daemon = True
client_t.start()

while True:
    sleep(.1)

