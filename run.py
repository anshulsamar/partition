import numpy as np
import random
from graphviz import Graph
import sys
import pickle
import os
import shutil

def clean_dirs(nodes_set):
    for node in nodes_set:
        direct = "node_" + str(node) + "/"
        if os.path.exists(direct):
            shutil.rmtree(direct)

# Read in vertex list and populate nodes
def read_vertices(filename, nodes_set, node_to_capacity_map, v_to_node_map, node_to_v_map, v_to_v_map):
    with open(filename, 'rb') as f:
        for line in f:
            v = int(line)
            if v not in v_to_node_map:
                space = [n for n in nodes_set if node_to_capacity_map[n]>0]
                if len(space) == 0:
                    print "Error: No space in nodes"
                    exit()
                node = random.choice(space)
                v_to_node_map[v] = node
                node_to_v_map[node].add(v)
                node_to_capacity_map[node] -= 1
                v_to_v_map[v] = set()

    return (node_to_capacity_map, v_to_node_map, node_to_v_map, v_to_v_map)
    #np.save("master_v_to_node.npy", v_to_node)


# Create folders for nodes, populate data
def create_nodes(nodes_set, node_to_port_map):
    for node in nodes:
        direct = "node_" + str(node) + "/"
        if not os.path.exists(direct):
            os.makedirs(direct)
        port = 10000 + node
        config = [port, nodes]
        pickle.dump(config, open(direct + "config.p",'wb'))
        pickle.dump(node_to_port_map, open(direct + "node_to_port.p",'wb'))


if (len(sys.argv) < 5):
    print("USAGE: python run.py [#nodes] [capacity] [vertices_file] [edges_file]")
    exit()

# Redundant data structures for easy access
N = int(sys.argv[1])                    # max nodes
nodes = set(range(0,N))                 # node identifiers
node_to_port = {}                       # node to port

max_capacity = int(sys.argv[2])         # max vertices/node
v_to_node = {}                          # vertex-node map
node_to_v = {}                          # node-vertex map
v_to_v = {}                             # vertex-vertex map
edges = set()                           # edge_list
capacity = {}                           # remaining capacity

vertices_file = sys.argv[3]
edges_file = sys.argv[4]
# Initialize nodes
for i in nodes:
    node_to_v[i] = set()
    capacity[i] = max_capacity
    node_to_port[i] = 10000 + i

clean_dirs(nodes)
(capacity, v_to_node, node_to_v, v_to_v) = read_vertices(vertices_file, nodes, \
                                                         capacity, v_to_node, node_to_v, \
                                                         v_to_v)
create_nodes(nodes, node_to_port)
