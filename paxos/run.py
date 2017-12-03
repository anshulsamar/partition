import numpy as np
import random
from graphviz import Graph
import sys
import pickle
import os

# Redundant data structures for easy access
N = int(sys.argv[1])                    # max nodes
nodes = set(range(0,N))                 # node identifiers
node_to_port = {}                       # node to port

# Initialize nodes
for i in nodes:
    node_to_port[i] = 10000 + i

# Create folders for nodes, populate data
def create_nodes():
    for node in nodes:
        direct = "node_" + str(node) + "/"
        if not os.path.exists(direct):
            os.makedirs(direct)
        port = 10000 + node
        config = [port, nodes]
        pickle.dump(config, open(direct + "config.p",'wb'))
        pickle.dump(node_to_port, open(direct + "node_to_port.p",'wb'))

create_nodes()
