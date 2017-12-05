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
import ast
import copy
import datetime
import numpy as np

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

    # Make sure that this vertex transfer message has all the tags
    #if IDTAG not in vertex_msg or \
    #   IDENDTAG not in vertex_msg or \
    #   EDGETAG not in vertex_msg or \
    #   EDGEENDTAG not in vertex_msg or \
    #   NODETAG not in vertex_msg or \
    #   NODEENDTAG not in vertex_msg:
    #     print("This message from node " + str(sender_node) + \
    #           " with sequence number " + str(seq_no) + \
    #           " does not have all the tags")
    #     return None

    # Extract the vertex id number
    id_first = vertex_msg.find(VERTEXIDTAG) + len(VERTEXIDTAG)        
    id_last = vertex_msg.find(VERTEXIDENDTAG)

    vertex_id = int(vertex_msg[id_first:id_last])

    # Extract the edge list that are connected to this vertex
    # Note that an edge is of the form v2 since we know
    # the other vertex (vertex_id)
    edge_first = vertex_msg.find(EDGETAG) + len(EDGETAG)
    edge_last = vertex_msg.find(EDGEENDTAG)

    edge_str = vertex_msg[edge_first:edge_last]
    edge_list = set(ast.literal_eval(edge_str))
    #edge_list = map(int, re.findall(r'\d+', edge_str))
    #edge_list = list(ast.literal_eval(edge_str))

    # Extract the node list that contain the edges
    node_first = vertex_msg.find(NODETAG) + len(NODETAG)
    node_last = vertex_msg.find(NODEENDTAG)

    node_str = vertex_msg[node_first:node_last]
    # https://stackoverflow.com/questions/13675942/converting-string-to-dict
    node_list = ast.literal_eval(node_str)
    #node_list = map(int, re.findall(r'\d+', node_str))

    # Extract the sender node's id
    sender_node_first = vertex_msg.find(SENDERNODETAG) + len(SENDERNODETAG)
    sender_node_last = vertex_msg.find(SENDERNODEENDTAG)

    sender_node = int(vertex_msg[sender_node_first:sender_node_last])

    # Extract the sender node's message sequence number
    seq_no_first = vertex_msg.find(SEQNOTAG) + len(SEQNOTAG)
    seq_no_last = vertex_msg.find(SEQNOENDTAG)

    seq_no = int(vertex_msg[seq_no_first:seq_no_last])

    return (vertex_id, edge_list, node_list, sender_node, seq_no) 


def server(this_node_id, vertex_set, edge_set, node_set, ack_no):
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

                direct = "node_" + str(this_node_id) + "/"
                # open config file?
                config = pickle.load(open(direct + "config.p",'rb'))
                # amount of vertices that can be added to this node
                capacity_left = config[0]
                seq_no = config[1]
                this_port = config[2]
                nodes = config[3]

                print("capacity_left: " + str(capacity_left))

                accepted = False
                # if capacity at this node is not full
                if capacity_left[this_node_id] > 0:
                    new_capacity_left = copy.deepcopy(capacity_left)
                    new_capacity_left[this_node_id] = capacity_left[this_node_id] - 1
                    #new_seq_no = seq_no + 1
                    new_config = [new_capacity_left, seq_no, this_port, nodes]
                    pickle.dump(new_config, open(direct + "config.p", 'wb'))

                    # need to update
                    #v_set = pickle.load(open(direct + 'v_set.p','rb'))
                    #v_to_v = pickle.load(open(direct + 'v_to_v.p','rb'))
                    #v_to_node = pickle.load(open(direct + 'v_to_node.p','rb'))

                    # Add vertex to the vertex set
                    vertex_set.add(vertex_id)
                    print("new vertex set: " + str(vertex_set))
                    pickle.dump(vertex_set, open(direct + 'v_set.p', 'wb'))

                    # Add edge to edge set
                    edge_set[vertex_id] = edge_list
                    print("new edge list: " + str(edge_set))
                    pickle.dump(edge_set, open(direct + 'v_to_v.p', 'wb'))

                    # Add node to node set
                    for v in node_list:
                        node_set[v] = node_list[v] 
                    node_set[vertex_id] = this_node_id
                    print("new node list: " + str(node_set))
                    pickle.dump(node_set, open(direct + 'v_to_node.p', 'wb'))
                    accepted = True
 
                ack_no[this_node_id] += 1
                # write to config
                # might have to use numpy instead of pickle

                # dump this metadata into vertex transfer msg file for
                # the client side to read and send back an ack to the 
                # sender node
                direct = "node_" + str(this_node_id) + "/"
                msg_meta = {"sender_node": sender_node, "seq_no": seq_no, "accepted": accepted}
                #pickle.dump(msg_meta, open(direct + "vertex_transfer_msg.p", "a"))
                np.save(msg_meta, direct + "vertex_transfer_msg.npy")
                
                

            print("Recv: " + data)
            sock.close()
        except:
            sleep(1)
            continue

def out_in (v):
    node = v_to_node[v]
    out_n = set()
    in_n = set()
    #print("v_to_v: " + str(v_to_v))
    #print("v_to_v for " + str(v) + ": " + str(v_to_v[v]))
    for vi in v_to_v[v]:
        if v_to_node[vi] == node:
            in_n.add(vi)
        else:
            out_n.add(vi)
    return out_n, in_n

def make_sender_id_tags(vertex_to_send, vertex_vertices, vertices_to_nodes, this_node_id, node_seq_no):
    '''
    Adds vertex id, vertices connected to this vertex (edges), and nodes that those vertices are at tags
    Note that vertex_vertices is of type list, not set 
    Adds node id and sequence number tags to the message
    '''

    msg = VERTEXIDTAG
    msg += str(vertex_to_send)
    msg += VERTEXIDENDTAG

    msg += EDGETAG
    msg += str(vertex_vertices)
    msg += EDGEENDTAG

    msg += NODETAG
    msg += str(vertices_to_nodes)
    msg += NODEENDTAG

    msg += SENDERNODETAG + str(this_node_id) + SENDERNODEENDTAG
    msg += SEQNOTAG + str(node_seq_no) + SEQNOENDTAG

    return msg

def client(this_node_id, vertex_set, node_seq_no, nodes, capacity_left, this_port):
    print("vertex_set: ", vertex_set)
    while True:
        # check to see if any vertex transfer messages received (we
        # can do this via vertex_transfer_msg.txt file)
        direct = "node_" + str(this_node_id) + "/"
        msg_metadata = pickle.load(open(direct + "vertex_transfer_msg.p", "rb"))
        #print("did this work?????????: " + str(msg_metadata))
        if msg_metadata is not None:
            print("msg_metadata bammmmmmmmmmmmmmmmmmmm: " )
            sender_node = msg_metadata["sender_node"]
            seq_no = msg_metadata["seq_no"]
            # TODO: make sure that the type of this is int
            # perhaps use "type(..)"

            print("Client: Attempting Ack --> Node: " + str(sender_node))
            #sock = psocket(blocking = True)
            #sock.pconnect('localhost', node_to_port[sender_node])
        
        # check every file in the txn_logs directory to see if any of the 
        # transactions have timed out
        # timeout is 10 seconds
        txn_dir = direct + "txn_logs/"
        if os.path.exists(os.getcwd() + "/" + txn_dir):
            for filename in os.listdir(os.getcwd() + "/" + txn_dir):
                txn = np.load(txn_dir + filename).item()
                now_ts = datetime.datetime.now()
                delta = now_ts - txn["ts"]
                # if we have not heard a reply back from the server that
                # we attempted to send this vertex to, add back the vertex
                # to our node's vertex set
                if delta.total_seconds() > 10:
                    os.remove(txn_dir + filename)
                    vertex_set.add(txn["vertex"])
       
        # need to make sure we have at least one vertex
        # to potentially transfer to another node
        if len(vertex_set) > 0:
            v = random.choice(list(vertex_set))
            #print("Picked vertex: " + str(v))
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
                
                    edges = list(v_to_v[v])

                    vertices_nodes = {}

                    for v2 in edges:
                        vertices_nodes[v2] = v_to_node[v2]

                    node_seq_no[this_node_id] += 1
                    new_config = [capacity_left, node_seq_no, this_port, nodes]
                    pickle.dump(new_config, open(direct + "config.p", 'wb'))

                    msg = make_sender_id_tags(v, edges, vertices_nodes, this_node_id, node_seq_no) 

                    print("Sending to port " + str(node_to_port[best_node]) + ": " + msg)

                    #msg = "Hello from Node: " + str(my_node)

                    # TODO: have to test this to see what happens when the node fails during a middle of a log write
                    # Also, should we do some ending character in the log file to know that its complete? otherwise
                    # we have no idea if a log file is corrupt or not
                    #vertex_transfer_file.close()
                    
                    print("vertex set old: " + str(vertex_set))
                    print("v: " + str(v))
                    # Remove the vertex from the node vertex list so that it's not chosen again
                    vertex_set.remove(v)

                    print("new vertex set: " + str(vertex_set))
                    sock.psend(msg)

                    # Add this transaction to the log file

                    txn_dir = direct + "txn_logs/"
                    if not os.path.exists(txn_dir):
                        os.makedirs(txn_dir)
                    #time_str = time.strftime("%Y%m%d-%H%M%S")
                    #log_name = time_str + ".p"
                    log_name = str(this_node_id) + "-" + str(node_seq_no[this_node_id]) + ".npy"
                    #vertex_transit_file = open(txn_dir + log_name, "wb")
                    msg_dict = {"vertex": v, "edges": edges, \
                                "vertices_nodes": vertices_nodes, "this_node_id": this_node_id, \
                                "node_seq_no": node_seq_no, "ts": datetime.datetime.now()}
                    #vertex_transit_file.write(msg_dict)
                    #pickle.dump(msg_dict, vertex_transit_file)
                    
                    #vertex_transit_file.close()
                    np.save(txn_dir + log_name, msg_dict)

                    sock.close()
                    break
                except:
                    print("exception!!!!!!")
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
    print "Vertex to Vertex:"
    print(v_to_v)
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
ack_no = config[4]

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
server_t = threading.Thread(target=server, args=(my_node, v_set, v_to_v, v_to_node, ack_no))
server_t.daemon = True
server_t.start()
print "Starting Client"
client_t = threading.Thread(target=client, args=(my_node, v_set, seq_no, nodes, capacity_left, my_port))
client_t.daemon = True
client_t.start()

while True:
    sleep(.1)

