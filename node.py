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
import time


VERTEXIDTAG = "<ID>"
VERTEXIDENDTAG = "<\ID>"
EDGETAG = "<EDGE>"
EDGEENDTAG = "<\EDGE>"
NODETAG = "<NODE>"
NODEENDTAG = "<\NODE>"

SENDERNODETAG = "<SENDERNODE>"
SENDERNODEENDTAG = "<\SENDERNODE>"

SEQNOTAG = "<SEQNO>"
SEQNOENDTAG = "<\SEQNO>"

def parse_vertex_info(vertex_msg):
    '''
    Parses a vertex message of the form:
    <ID>10<\ID><EDGE>1, 2, 3<\EDGE><NODE>1, 3, 4<\NODE>

    This a vertex message one node sends to another to transfer
    the vertex to that node

    '''

    # Extract the sender node's id
    sender_node_first = vertex_msg.find(SENDERNODETAG) + len(SENDERNODETAG)
    sender_node_last = vertex_msg.find(SENDERNODEENDTAG)

    sender_node = int(vertex_msg[sender_node_first:sender_node_last])

    # Extract the sender node's message sequence number
    seq_no_first = vertex_msg.find(SEQNOTAG) + len(SEQNOTAG)
    seq_no_last = vertex_msg.find(SEQNOENDTAG)

    seq_no = int(vertex_msg[seq_no_first:seq_no_last])

    # Make sure that this vertex transfer message has all the tags
    if IDTAG not in vertex_msg or \
       IDENDTAG not in vertex_msg or \
       EDGETAG not in vertex_msg or \
       EDGEENDTAG not in vertex_msg or \
       NODETAG not in vertex_msg or \
       NODEENDTAG not in vertex_msg:
         print("This message from node " + str(sender_node) + \
               " with sequence number " + str(seq_no) + \
               " does not have all the tags")
         return None

    # Extract the vertex id number
    id_first = vertex_msg.find(VERTEXIDTAG) + len(VERTEXIDTAG)        
    id_last = vertex_msg.find(VERTEXIDENDTAG)

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

    return (vertex_id, edge_list, node_list, sender_node, seq_no) 


def server(this_node_id):
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
            # parse the vertex transfer message
            parsed_data = parse_vertex_info(data)
            if parsed_data is not None:
                vertex_id = parsed_data[0]
                edge_list = parsed_data[1]
                node_list = parsed_data[2]
                sender_node = parsed_data[3]
                seq_no = parsed_data[4]

                print("vertex id: " + str(vertex_id))
                print("edge list: " + str(edge_list))
                print("node list: " + str(node_list))
                print("sender node: " + str(sender_node))
                print("seq no: " + str(seq_no))

                # dump this metadata into vertex transfer msg file for
                # the client side to read and send back an ack to the 
                # sender node
                direct = "node_" + str(this_node_id) + "/"
                msg_meta = {"sender_node": sender_node, "seq_no": seq_no}
                pickle.dump(msg_meta, open(direct + "vertex_transfer_msg.p", "a"))
                

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

def add_sender_id_tags(this_node_id, node_seq_no, msg):
    '''
    Adds node id and sequence number tags to the message
    '''

    SENDERNODETAG = "<SENDERID>"
    SENDERNODEENDTAG = "<\SENDERID>"

    SEQNOTAG = "<SEQNO>"
    SEQNOENDTAG = "<\SEQNO>"

    msg += SENDERNODETAG + str(this_node_id) + SENDERNODEENDTAG
    msg += SEQNOTAG + str(node_seq_no) + SEQNOENDTAG

    return msg

def client(this_node_id, node_seq_no, vertex_set):
    while True:
        # check to see if any vertex transfer messages received (we
        # can do this via vertex_transfer_msg.txt file)
        direct = "node_" + str(this_node_id) + "/"
        msg_metadata = pickle.load(open(direct + "vertex_transfer_msg.p", "rb"))
 

        # need to make sure we have at least one vertex
        # to potentially transfer to another node
        if len(vertex_set) > 0:
            v = random.choice(list(vertex_set))
            print("Picked vertex: " + str(v))
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

            # NOTE: why check for capacity > 0? i thought maybe that was
            # for the server side? - naokieto
            if diff > 0:# and capacity > 0:        
                try:
                    # connects to node
                    print("Client: Attempting --> Node: " + str(best_node))
                    sock = psocket(blocking = True)
                    sock.pconnect('localhost', node_to_port[best_node])
                    print("Client: Connected!")
                
                    # send port number to master
                    msg = raw_input()

                    msg = add_sender_id_tags(msg) 

                    print("Sending to port " + str(node_to_port[best_node]) + ": " + msg)

                    #msg = "Hello from Node: " + str(my_node)
                    time_str = time.strftime("%Y%m%d-%H%M%S")
                    log_name = time_str + ".txt"

                    vertex_transfer_file = open(log_name, "w")

                    # write ahead logging
                    vertex_transfer_file.write(msg)

                    # TODO: have to test this to see what happens when the node fails during a middle of a log write
                    # Also, should we do some ending character in the log file to know that its complete? otherwise
                    # we have no idea if a log file is corrupt or not
                    vertex_transfer_file.close()

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
# amount of vertices that can be added to this node
capacity_left = config[0]
seq_no = config[1]
my_port = config[2]
nodes = config[3]

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
server_t = threading.Thread(target=server, args=(my_node,))
server_t.daemon = True
server_t.start()
print "Starting Client"
client_t = threading.Thread(target=client, args=(my_node, v_set, seq_no))
client_t.daemon = True
client_t.start()

while True:
    sleep(.1)

