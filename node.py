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

ACCEPTTAG = "<ACCEPT>"
ACCEPTENDTAG = "<\ACCEPT>"

RECVRNODETAG = "<RECVRNODE>"
RECVRNODEENDTAG = "<\RECVRNODE>"

def parse_vertex_info(vertex_msg):
    '''
    Parses a vertex message of the form:
    <ID>10<\ID><EDGE>1, 2, 3<\EDGE><NODE>1, 3, 4<\NODE>

    This a vertex message one node sends to another to transfer
    the vertex to that node

    '''

    # Make sure that this vertex transfer message has all the tags
    if VERTEXIDTAG not in vertex_msg or \
       VERTEXIDENDTAG not in vertex_msg or \
       EDGETAG not in vertex_msg or \
       EDGEENDTAG not in vertex_msg or \
       NODETAG not in vertex_msg or \
       NODEENDTAG not in vertex_msg or \
       SENDERNODETAG not in vertex_msg or \
       SENDERNODEENDTAG not in vertex_msg or \
       SEQNOTAG not in vertex_msg or \
       SEQNOENDTAG not in vertex_msg:
         #print("This message from node " + str(sender_node) + \
         #      " with sequence number " + str(seq_no) + \
         #      " does not have all the tags")
         return None

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

    seq_no_str = vertex_msg[seq_no_first:seq_no_last]
    seq_no = list(ast.literal_eval(seq_no_str)) #int(vertex_msg[seq_no_first:seq_no_last])

    return (vertex_id, edge_list, node_list, sender_node, seq_no) 

def parse_ack(ack_msg):
    if ACCEPTTAG not in ack_msg or \
       ACCEPTENDTAG not in ack_msg or \
       SEQNOTAG not in ack_msg or \
       SEQNOENDTAG not in ack_msg or \
       RECVRNODETAG not in ack_msg or \
       RECVRNODEENDTAG not in ack_msg:
         return None

    accept_first = ack_msg.find(ACCEPTTAG) + len(ACCEPTTAG)
    accept_last = ack_msg.find(ACCEPTENDTAG)

    accept_str = ack_msg[accept_first:accept_last]
    if accept_str.lower() == 'true':
        accept = True
    else:
        accept = False

    # Extract the sender node's message sequence number (this node's seq no)
    # this is to find the transaction log that corresponds with this number
    # and remove it
    seq_no_first = ack_msg.find(SEQNOTAG) + len(SEQNOTAG)
    seq_no_last = ack_msg.find(SEQNOENDTAG)

    seq_no_str = ack_msg[seq_no_first:seq_no_last]
    seq_no = list(ast.literal_eval(seq_no_str))

    recvr_node_first = ack_msg.find(RECVRNODETAG) + len(RECVRNODETAG)
    recvr_node_last = ack_msg.find(RECVRNODEENDTAG)

    recvr_node = int(ack_msg[recvr_node_first:recvr_node_last])

    return (accept, seq_no, recvr_node)

def server(this_node_id, vertex_set, edge_set, node_set, ack_no):

    direct = "node_" + str(this_node_id) + "/"
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
            print("data: " + data)
            # parse ack message
            parsed_ack = parse_ack(data)
            if parsed_ack is not None:
                accept = parsed_ack[0]
                seq_no = parsed_ack[1]
                recvr_node = parsed_ack[2]

                txn_dir = direct + "txn_logs/"
                log_name = str(recvr_node) + "-" + str(seq_no[recvr_node]) + ".npy"

                if not accept:
                    with np.load(txn_dir + log_name).item() as txn:
                        # add back the vertex
                        vertex_to_add_back = txn["vertex"]

                        vertex_set.add(vertex_to_add_back)
                        pickle.dump(vertex_set, open(direct + "v_set.p",'wb'))
                        #np.save(direct + "v_set.npy", vertex_set)

                        v_to_node[vertex_to_add_back] = this_node_id
                        np.save(direct + "v_to_node.npy", v_to_node)

                # delete the transaction log
                txn_dir = direct + "txn_logs/"
                log_name = str(recvr_node) + "-" + str(seq_no[recvr_node]) + ".npy"
                os.remove(txn_dir + log_name)
            # parse the vertex transfer message
            parsed_data = parse_vertex_info(data)
            if parsed_data is not None:
                vertex_id = parsed_data[0]
                sender_v_to_v = parsed_data[1]
                sender_node_list = parsed_data[2]
                sender_node = parsed_data[3]
                sender_seq_no = parsed_data[4]

                print("vertex id: " + str(vertex_id))
                print("sender edge list: " + str(sender_v_to_v))
                print("sender node list: " + str(sender_node_list))
                print("sender node: " + str(sender_node))
                print("sender seq no: " + str(sender_seq_no))

                print("config file path: " + direct + "config.npy")
                # open config file?
                #config = pickle.load(open(direct + "config.p",'rb'))
                config = np.load(direct + "config.npy")
                #with np.load(direct + "config.npy") as config:
                print("we go tconfig!!!: " + str(config))
                # amount of vertices that can be added to this node
                capacity_left = config[0]
                this_seq_no = config[1]
                this_port = config[2]
                this_nodes = config[3]

                del config
                print("capacity_left: " + str(capacity_left))
                print("this_nodes: " + str(this_nodes))

                accepted = False
                # if capacity at this node is not full
                if capacity_left[this_node_id] > 0:
                    print("what what")
                    new_capacity_left = copy.deepcopy(capacity_left)
                    new_capacity_left[this_node_id] = capacity_left[this_node_id] - 1
                    #new_seq_no = seq_no + 1
                    print("new config!!!!")
                    new_config = [new_capacity_left, this_seq_no, this_port, this_nodes]
                    #pickle.dump(new_config, open(direct + "config.p", 'wb'))
                    print("lakers")
                    np.save(direct + "config.npy", new_config)
                    print("losers")
                    # need to update
                    
                    # Add vertex to this node's vertex set
                    vertex_set.add(vertex_id)
                    print("new vertex set: " + str(vertex_set))
                    pickle.dump(vertex_set, open(direct + 'v_set.p', 'wb'))
                    #np.save(direct + "v_set.npy", vertex_set)

                    # Add edge to this node's edge set
                    edge_set[vertex_id] = sender_v_to_v
                    print("new edge list: " + str(edge_set))
                    #pickle.dump(edge_set, open(direct + 'v_to_v.p', 'wb'))
                    np.save(direct + "v_to_v.npy", edge_set)

                    # Add node to this node's v to node set
                    for v in sender_node_list:
                        node_set[v] = sender_node_list[v] 
                    node_set[vertex_id] = this_node_id
                    print("new node list: " + str(node_set))
                    #pickle.dump(node_set, open(direct + 'v_to_node.p', 'wb'))
                    np.save(direct + "v_to_node.npy", node_set)

                    # save to master v_to_node for graphing
                    #master_v_to_node = np.load("master_v_to_node.npy").item()
                    with np.load("master_v_to_node.npy").item() as  master_v_to_node:
                        master_v_to_node[vertex_id] = this_node_id

                        np.save("master_v_to_node.npy", master_v_to_node)

                    accepted = True

                    print("done!!!") 
                ack_no[this_node_id] += 1
                # write to config
                # might have to use numpy instead of pickle

                # dump this metadata into vertex transfer msg file for
                # the client side to read and send back an ack to the 
                # sender node
                direct = "node_" + str(this_node_id) + "/"
                ack_dir = direct + "ack_msg/"

                if not os.path.exists(ack_dir):
                    os.makedirs(ack_dir)
                msg_fname = str(this_node_id) + "-" + str(ack_no[this_node_id]) + ".npy"
                msg_meta = {"sender_node": sender_node, "seq_no": seq_no, "accepted": accepted}
                #pickle.dump(msg_meta, open(direct + "vertex_transfer_msg.p", "a"))
                np.save(ack_dir + msg_fname, msg_meta)

            print("Recv: " + data)
            sock.close()
        except:
            sleep(1)
            continue

def out_in (v, v_to_node_map, v_to_v_map):
    node = v_to_node_map[v]
    out_n = set()
    in_n = set()
    #print("v_to_v: " + str(v_to_v))
    #print("v_to_v for " + str(v) + ": " + str(v_to_v[v]))
    for vi in v_to_v_map[v]:
        if v_to_node_map[vi] == node:
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

def make_ack_msg(accepted, seq_no, node_id):
    msg = ACCEPTTAG
    msg += str(accepted)
    msg += ACCEPTENDTAG

    msg += SEQNOTAG + str(seq_no) + SEQNOENDTAG
    msg += RECVRNODETAG + str(node_id) + RECVRNODEENDTAG

    return msg

def client(this_node_id, node_seq_no, nodes, capacity_left, this_port):
    #print("vertex_set: ", vertex_set)
    while True:
        # check to see if any vertex transfer messages received (we
        # can do this via vertex_transfer_msg.txt file)
        direct = "node_" + str(this_node_id) + "/"
        ack_dir = direct + "ack_msg/"

        #vertex_set = np.load(direct + "v_set.npy")
        v_file = open(direct + "v_set.p", "rb")
        vertex_set = pickle.load(v_file)
        v_file.close()
        #print("vertex set!!: " + str(vertex_set))
        #with np.load(direct + "v_to_v.npy").item() as this_v_to_v:
        #    with np.load(direct + "v_to_node.npy").item() as this_v_to_node:

        if os.path.exists(ack_dir):
            for filename in os.listdir(ack_dir):
                #msg_metadata = np.load(ack_dir + filename).item()
                with np.load(ack_dir + filename).item() as msg_metadata:
                    #if msg_metadata is not None:
                    #print("msg_metadata bammmmmmmmmmmmmmmmmmmm: " + str(msg_metadata))
                    sender_node = msg_metadata["sender_node"]
                    seq_no = msg_metadata["seq_no"]
                    accepted = msg_metadata["accepted"]
                    # TODO: make sure that the type of this is int
                    # perhaps use "type(..)"

                    print("Client: Attempting Ack --> Node: " + str(sender_node))
                    sock = psocket(blocking = True)
                    sock.pconnect('localhost', node_to_port[sender_node])
                    #ack_data = {"accepted": accepted, "seq_no": seq_no, "receiver_node": this_node_id}
                    ack_msg = make_ack_msg(accepted, seq_no, this_node_id)

                    
                    sock.psend(ack_msg)
                    sock.close()

        # check every file in the txn_logs directory to see if any of the 
        # transactions have timed out
        # timeout is 10 seconds
        txn_dir = direct + "txn_logs/"
        if os.path.exists(os.getcwd() + "/" + txn_dir):
            for filename in os.listdir(os.getcwd() + "/" + txn_dir):
                #txn = np.load(txn_dir + filename).item()
                with np.load(txn_dir + filename).item() as txn:
                    this_v_to_v = np.load(direct + "v_to_v.npy").item()
                    this_v_to_node = np.load(direct + "v_to_node.npy").item()
                    now_ts = datetime.datetime.now()
                    delta = now_ts - txn["ts"]
                    # if we have not heard a reply back from the server that
                    # we attempted to send this vertex to, add back the vertex
                    # to our node's vertex set
                    if delta.total_seconds() > 10:
                        os.remove(txn_dir + filename)
                        vertex_to_add_back = txn["vertex"]

                        vertex_set.add(vertex_to_add_back)
                        pickle.dump(vertex_set, open(direct + 'v_set.p', 'wb'))
                        #np.save(direct + "v_set.npy", vertex_set)

                        this_v_to_node[vertex_to_add_back] = this_node_id
                        np.save(direct + "v_to_node.npy", this_v_to_node)

                        master_v_to_node = np.load("master_v_to_node.npy").item()
                        master_v_to_node[vertex_to_add_back] = this_node_id
                        np.save("master_v_to_node.npy", master_v_to_node)
                        del master_v_to_node
                    del this_v_to_v
                    del this_v_to_node 
       
        # need to make sure we have at least one vertex
        # to potentially transfer to another node
        if len(vertex_set) > 0:
            v = random.choice(list(vertex_set))
            #print("Picked vertex: " + str(v) + " out of " + str(vertex_set))
            #print("v_to_v: " + str(v_to_v) + " v: " + str(v))
            #print("v_to_node: " + str(this_v_to_node))

            this_v_to_v = np.load(direct + "v_to_v.npy").item()
            this_v_to_node = np.load(direct + "v_to_node.npy").item()

            # out and in neighbors
            out_n, in_n = out_in(v, this_v_to_node, this_v_to_v)
            # out edges by node
            out_counts = {}
            for n in nodes:
                out_counts[n] = 0
            for vi in out_n:
                out_node = this_v_to_node[vi]
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
                        vertices_nodes[v2] = this_v_to_node[v2]

                    node_seq_no[this_node_id] += 1
                    new_config = [capacity_left, node_seq_no, this_port, nodes]
                    #pickle.dump(new_config, open(direct + "config.p", 'wb'))
                    

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
                    v_to_node[v] = best_node
                    pickle.dump(vertex_set, open(direct + 'v_set.p', 'wb'))
                    #np.save(direct + "v_set.npy", vertex_set)
                    np.save(direct + "v_to_node.npy", v_to_node)
                    master_v_to_node = np.load("master_v_to_node.npy")
                    master_v_to_node[v] = best_node
                    np.save("master_v_to_node.npy", master_v_to_node)
                    del master_v_to_node

                    print("new vertex set: " + str(vertex_set))
                    sock.psend(msg)

                    # Add this transaction to the log file

                    txn_dir = direct + "txn_logs/"
                    if not os.path.exists(txn_dir):
                        os.makedirs(txn_dir)
                    #time_str = time.strftime("%Y%m%d-%H%M%S")
                    #log_name = time_str + ".p"
                    log_name = str(best_node) + "-" + str(node_seq_no[best_node]) + ".npy"
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
            del this_v_to_v
            del this_v_to_node

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

VERTEXTAG = "<VERTEX>"
OLDNODETAG = "<OLDNODE>"
NEWNODETAG = "<NEWNODE>"

def out_in (v, v_to_node_map, v_to_v_map):
    node = v_to_node_map[v]
    out_n = set()
    in_n = set()
    for vi in v_to_v_map[v]:
        if v_to_node_map[vi] == node:
            in_n.add(vi)
        else:
            out_n.add(vi)
    return out_n, in_n

def suggest_transaction (this_node, vertex_set, this_v_to_v, this_v_to_node, this_node_to_capacity):

    nodes = this_node_to_capacity.keys()
    txn_msg = "NONE"
    # need to make sure we have at least one vertex
    # to potentially transfer to another node
    if len(vertex_set) > 0:
        v = random.choice(list(vertex_set))

        # out and in neighbors
        out_n, in_n = out_in(v, this_v_to_node, this_v_to_v)
        # out edges by node
        out_counts = {}
        for n in nodes:
            out_counts[n] = 0
        for vi in out_n:
            out_node = this_v_to_node[vi]
            out_counts[out_node] = out_counts[out_node] + 1
        best_node = max(out_counts.iterkeys(),
                        key=lambda k: out_counts[k])
        # diff is num_outedges - num_inedges
        diff = out_counts[best_node] - len(in_n)

        # check that the node we want to send this vertex to has capacity
        if diff > 0 and this_node_to_capacity[best_node] > 0:
            txn_msg = VERTEXTAG + str(v) + OLDNODETAG + str(this_node) + \
                      NEWNODETAG + str(best_node)        
    return txn_msg

def parse_transaction(txn):

    if VERTEXTAG not in txn or \
       OLDNODETAG not in txn or \
       NEWNODETAG not in txn:
        return None
    
    # Get the vertex id
    vertex_first = txn.find(VERTEXTAG) + len(VERTEXTAG)        
    vertex_last = txn.find(OLDNODETAG)
    vertex_id = int(txn[vertex_first:vertex_last])

    # Get the sender node id
    sender_first = txn.find(OLDNODETAG) + len(OLDNODETAG)
    sender_last = txn.find(NEWNODETAG)
    sender_node = int(txn[sender_first:sender_last])

    # Get the recipient node id
    recv_first = txn.find(NEWNODETAG) + len(NEWNODETAG)
    recv_node = int(txn[recv_first:])

    return (vertex_id, sender_node, recv_node) 

def execute_transaction (txn, this_node, vertex_set, this_v_to_node, this_node_to_capacity):
    if txn == "NONE":
        return (vertex_set, this_v_to_node, this_node_to_capacity)
    
    res = parse_transaction(txn)

    if res is None:
        return (vertex_set, this_v_to_node, this_node_to_capacity)

    (v, snd_node, recv_node) = res

    # Make the updates to the local data structures
    if snd_node == this_node:
        vertex_set.remove(v)
    elif recv_node == this_node:
        vertex_set.add(v)

    this_v_to_node[v] = recv_node
    this_node_to_capacity[snd_node] += 1
    this_node_to_capacity[recv_node] -= 1

    return (vertex_set, this_v_to_node, this_node_to_capacity)

vertex_set_3 = set([22, 23, 24])
vertex_set_1 = set([20, 25])
vertex_set_2 = set([21, 26])
v_to_v = {20:[21], 21:[20, 25, 26], 22:[23], 23:[22, 24], 24:[23], 25:[21], 26:[21]}
this_v_to_node = {20:1, 21:2, 22:3, 23:3, 24:3, 25:1, 26:2}
this_node_to_capacity = {1:2, 2:2, 3:1}

print(suggest_transaction(1, vertex_set_1, v_to_v, this_v_to_node, this_node_to_capacity))
print(execute_transaction("<VERTEX>20<OLDNODE>1<NEWNODE>2", 3, vertex_set_3, this_v_to_node, this_node_to_capacity))

print(execute_transaction("<VERTEX>20<OLDNODE>1<NEWNODE>2", 2, vertex_set_2, this_v_to_node, this_node_to_capacity))


'''
    
if (len(sys.argv) < 2):
    print("USAGE: python node.py [node_id]")
    exit()

my_node = int(sys.argv[1])
direct = "node_" + str(my_node) + "/"
#config = pickle.load(open(direct + 'config.p','rb'))
config = np.load(direct + "config.npy")
# amount of vertices that can be added to this node
capacity_left = config[0]
seq_no = config[1]
my_port = config[2]
nodes = config[3]
ack_no = config[4]

# data structures for graph
v_set = pickle.load(open(direct + 'v_set.p','rb'))
#v_to_v = pickle.load(open(direct + 'v_to_v.p','rb'))
#v_to_node = pickle.load(open(direct + 'v_to_node.p','rb'))
#v_set = np.load(direct + "v_set.npy")
v_to_v = np.load(direct + "v_to_v.npy").item()
v_to_node = np.load(direct + "v_to_node.npy").item()
print_data_structures()

# keep track of other node/ports
#node_to_port = pickle.load(open(direct + 'node_to_port.p','rb'))
node_to_port = np.load(direct + "node_to_port.npy").item()

# catch node up to speed
redo_log ()
print_graph(direct + str(my_node))

# start client threads
print "Starting Server"
server_t = threading.Thread(target=server, args=(my_node, v_set, v_to_v, v_to_node, ack_no))
server_t.daemon = True
server_t.start()
print "Starting Client"
client_t = threading.Thread(target=client, args=(my_node, seq_no, nodes, capacity_left, my_port))
client_t.daemon = True
client_t.start()

while True:
    sleep(.1)
'''
