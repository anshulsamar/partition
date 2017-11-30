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
import random
import re


def parse_vertex_info(vertex_msg):
    '''
    Parses a vertex message of the form:
    <ID>10<\ID><EDGE>1, 2, 3<\EDGE><NODE>1, 3, 4<\NODE>

    This a vertex message one node sends to another to transfer
    the vertex to that node

    '''
    
    IDTAG = "<ID>"
    IDENDTAG = "<\ID>"
    EDGETAG = "<EDGE>"
    EDGEENDTAG = "<\EDGE>"
    NODETAG = "<NODE>"
    NODEENDTAG = "<\NODE>"

    if IDTAG not in vertex_msg or \
       IDENDTAG not in vertex_msg or \
       EDGETAG not in vertex_msg or \
       EDGEENDTAG not in vertex_msg or \
       NODETAG not in vertex_msg or \
       NODEENDTAG not in vertex_msg:
         print("This message does not have all the tags")
         return None

    # Extract the vertex id number
    id_first = vertex_msg.find(IDTAG) + len(IDTAG)        
    id_last = vertex_msg.find(IDENDTAG)

    vertex_id = int(vertex_msg[id_first:id_last])

    # Extract the edge list that are connected to this vertex
    edge_first = vertex_msg.find(EDGETAG) + len(EDGETAG)
    edge_last = vertex_msg.find(EDGEENDTAG)

    edge_str = vertex_msg[edge_first:edge_last]
    edge_list = map(int, re.findall(r'\d+', edge_str))

    # Extract the node list that contain the edges
    node_first = vertex_msg.find(NODETAG) + len(NODETAG)
    node_last = vertex_msg.find(NODEENDTAG)

    node_str = vertex_msg[node_first:node_last]
    node_list = map(int, re.findall(r'\d+', node_str))

    return (vertex_id, edge_list, node_list) 


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
            parsed_data = parse_vertex_info(data)
            if parsed_data is not None:
                vertex_id = parsed_data[0]
                edge_list = parsed_data[1]
                node_list = parsed_data[2]

                print("vertex id: " + str(vertex_id))
                print("edge list: " + str(edge_list))
                print("node list: " + str(node_list))

            print("Recv: " + data)
            sock.close()
        except:
            sleep(1)
            continue

def out_in (v):
    node = v_to_node[v]
    out_n = set()
    in_n = set()
    for vi in v_to_v[v]:
        if v_to_node[vi] == node:
            in_n.add(vi)
        else:
            out_n.add(vi)
    return out_n, in_n

def client():
    while True:
        v = random.choice(list(v_set))
        print "Picked vertex: " + str(v)
        # out and in neighbors
        out_n, in_n = out_in(v)
        # out edges by node
        out_counts = {}
        for n in nodes:
            out_counts[n] = 0
        for vi in out_n:
            out_node = v_to_node[vi]
            out_counts[out_node] = out_counts[out_node] + 1
        best_node = max(out_counts.iterkeys(),
                        key=lambda k: out_counts[k])
        # diff is num_outedges - num_inedges
        diff = out_counts[best_node] - len(in_n)

        if diff > 0 and capacity > 0:        
            try:
                # connects to node
                print "Client: Attempting --> Node: " + str(best_node)
                sock = psocket(blocking = True)
                sock.pconnect('localhost', node_to_port[best_node])
                print "Client: Connected!"
            
                # send port number to master
                msg = raw_input()
                #msg = "Hello from Node: " + str(my_node)
                sock.psend(msg)
                sock.close()
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

