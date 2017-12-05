import numpy as np
import random
from graphviz import Graph
import sys
import pickle
import os
import shutil

# Redundant data structures for easy access
N = 5                                   # max nodes
nodes = set(range(0,N))                 # node identifiers
node_to_port = {}                       # node to port
max_capacity = 5                        # max vertices/node
v_to_node = {}                          # vertex-node map
node_to_v = {}                          # node-vertex map
v_to_v = {}                             # vertex-vertex map
edges = set()                           # edge_list
capacity = {}                           # remaining capacity
threshold = 0                           # partition thresh
# NOTE: Added by naokieto
# Maybe initial sequence number should be initialized to avoid seq num 0
# attacks
seq_no = [0] * 5                        # sequence number of message
ack_no = [0] * 5                        # acknowledgement number

# Initialize nodes
for i in nodes:
    node_to_v[i] = set()
    capacity[i] = max_capacity
    node_to_port[i] = 10000 + i

# Read in vertex list and populate nodes
def read_vertices(filename):
    with open(filename, 'rb') as f:
        for line in f:
            v = int(line)
            if v not in v_to_node:
                space = [n for n in nodes if capacity[n]>0]
                if len(space) == 0:
                    print "Error: No space in nodes"
                    exit()
                node = random.choice(space)
                v_to_node[v] = node
                node_to_v[node].add(v)
                capacity[node] = capacity[node] - 1
                v_to_v[v] = set()

# Read in edge list
def read_edges(filename):
    with open(filename, 'rb') as f:
        for line in f:
            v1, v2 = line.split(',')
            v1 = int(v1)
            v2 = int(v2)
            v_to_v[v1].add(v2)
            v_to_v[v2].add(v1)
            edges.add((v1,v2))

# Prints graph and nodes (based on graphviz ex)
def print_graph (fname):
    g = Graph('G', filename=fname, format='png')
    c = {}

    for node in nodes:
        # Note 'cluster_' prefix required naming
        node_name = 'cluster_' + str(node)        
        c[node] = Graph(name=node_name)
        c[node].attr(style='filled')
        c[node].attr(color='lightgrey')
        c[node].node_attr.update(style='filled', color='white')
        for v in node_to_v[node]:
            c[node].node(str(v))                  
        c[node].attr(fontsize='8')
        c[node].attr(label=node_name)
        g.subgraph(c[node])

    for e in edges:
        g.edge(str(e[0]),str(e[1]))
    g.render(fname)

# Print graph data structures
def print_data_structures():
    print "Vertex To Node:"
    print v_to_node
    print "Node to Vertex"
    print node_to_v
    print "Vertex to Vertex"
    print v_to_v
    print "Edges"
    print edges
    print "Capacities"
    print capacity

# Create folders for nodes, populate data
def create_nodes():
    for node in nodes:
        direct = "node_" + str(node) + "/"
        if not os.path.exists(direct):
            os.makedirs(direct)
        port = 10000 + node
        config = [capacity, seq_no, port, nodes, ack_no]
        pickle.dump(config, open(direct + "config.p",'wb'))
        pickle.dump(node_to_v[node], open(direct + "v_set.p",'wb'))

        vertex_transfer_fn = "vertex_transfer_msg.p"
        # create file for holding the vertex message transfer sender info
        # maybe pickle dump None to the file
        vertex_transfer_sender = open(direct + vertex_transfer_fn, 'wb')

        pickle.dump(None, vertex_transfer_sender)
        vertex_transfer_sender.close()

        # select only vertices on this node
        v_to_v_s = {}
        for v in v_to_v:
            if v in node_to_v[node]:
                v_to_v_s[v] = v_to_v[v]
        pickle.dump(v_to_v_s, open(direct + "v_to_v.p",'wb'))
        # store v to node only for vertices node knows about
        v_to_node_s = {}
        for k,v in v_to_v_s.iteritems():
            if k not in v_to_node_s:
                v_to_node_s[k] = v_to_node[k]
            for vi in v:
                if vi not in v_to_node_s:
                    v_to_node_s[vi] = v_to_node[vi]
        pickle.dump(v_to_node_s, open(direct + "v_to_node.p",'wb'))
        pickle.dump(node_to_port, open(direct + "node_to_port.p",'wb'))

def clean_dirs():
    for node in nodes:
        direct = "node_" + str(node) + "/"
        if os.path.exists(direct):
            txn_dir = direct + "txn_logs/"
            ack_dir = direct + "ack_msg/"
            if os.path.exists(txn_dir):
                shutil.rmtree(txn_dir)
            if os.path.exists(ack_dir):
                shutil.rmtree(ack_dir)

if (len(sys.argv) < 2):
    print("USAGE: python run.py [#nodes] [capacity] [file1] [file2]")
    exit()

read_vertices(sys.argv[3])
read_edges(sys.argv[4])
print_graph('starting_config')
create_nodes()
clean_dirs()
