# Reads in vertex list. Format:
# <vertex_id>
# Reads in undirected edge list. Format:
# <vertex_id>,<vertex_id>
# Randomly assigns vertices to N nodes
# Node tracks each vertex and undirected edge
# and which vertex & node edge goes to

import numpy as np
import random
from graphviz import Graph
import sys

# Redundant data structures for easy access
N = 5                # max nodes
nodes = range (0,N)  # node identifiers
capacity = 3         # max vertices/node
v_to_node = {}       # vertex - node mapping
node_to_v = {}       # node - vertex mapping
v_to_v = {}          # vertex - vertex mapping
edges = set()        # edge_list

# Initialize nodes
for i in nodes:
    node_to_v[i] = set()

# Read in vertex list and populate nodes
def read_vertices(filename):
    with open(filename, 'rb') as f:
        for line in f:
            v = int(line)
            if v not in v_to_node:
                node = random.choice(nodes)
                v_to_node[v] = node
                node_to_v[node].add(v)
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
def print_graph ():
    g = Graph('G', filename='cluster.gv', format='png')
    c = [None] * N

    for i in range(0,N):
        node_name = 'cluster_' + str(nodes[i])        #cluster name req
        c[i] = Graph(name=node_name)
        c[i].attr(style='filled')
        c[i].attr(color='lightgrey')
        c[i].node_attr.update(style='filled', color='white')
        for v in node_to_v[nodes[i]]:
            c[i].node(str(v))
        c[i].attr(fontsize='8')
        c[i].attr(label=node_name)
        g.subgraph(c[i])

    for e in edges:
        g.edge(str(e[0]),str(e[1]))
    g.render('cluster.gv')

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

def stats():
    

if len(sys.argv) < 3:
    print("Usage: python partition.py [vertex_file] [edges_file]")
    exit()

read_vertices(sys.argv[1])
read_edges(sys.argv[2])
print_data_structures()

print_graph()
