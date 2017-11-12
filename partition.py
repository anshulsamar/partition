# Reads in vertex list. Format: <vertex_id>. Reads in
# undirected edge list. Format: <vertex_id>,<vertex_id>
# Randomly assigns vertices to N nodes. 

import numpy as np
import random
from graphviz import Graph
import sys

# Redundant data structures for easy access
N = 3                                   # max nodes
nodes = set(range(0,N))                 # node identifiers
max_capacity = 10                       # max vertices/node
v_to_node = {}                          # vertex-node map
node_to_v = {}                          # node-vertex map
v_to_v = {}                             # vertex-vertex map
edges = set()                           # edge_list
capacity = {}                           # remaining capacity
threshold = 0                           # partition thresh

# Initialize nodes
for i in nodes:
    node_to_v[i] = set()
    capacity[i] = max_capacity

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

# Returns neighbors outsidee (out) and neigbhors inside (in)
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
            
# Calculates basic statistics
def stats():
    for node in nodes:
        vertices = node_to_v[node]
        if len(vertices) == 0: continue
        # total edges within node
        in_edges = 0
        # total edges leaving node
        out_edges = 0
        # avg across vertices of out neighbors
        total_avg = 0
        for v in vertices:
            out_n, in_n = out_in(v)
            v_out_node = len(out_n)
            v_in_node = len(in_n)
            # frac of out neighbors
            avg_out = float(v_out_node)/len(v_to_v[v])
            # update global frac
            total_avg = total_avg + avg_out
            # update edge counts
            in_edges = in_edges + v_in_node
            out_edges = out_edges + v_out_node

        total_avg = total_avg/len(vertices)
        print "Node: " + str(node)
        print "\tout edges: " + str(out_edges)
        print "\tin edges: " + str(in_edges)
        print "\tavg out: " + str(total_avg)

# Randomly picks node. Attempts to move a random vertex
# to better node if space is available. Simple
# hueristic - if v has most neighbors in n, move to node
# n. 
def partition_a ():
    node = random.choice(list(nodes))
    v = random.choice(list(node_to_v[node]))
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
    # diff = num_outedges - num_inedges
    diff = out_counts[best_node] - len(in_n)
    # move if space in best_node
    if diff > threshold and capacity[best_node] > 0:
        print str(v) + ": " + str(node) + " -> " + str(best_node)
        v_to_node[vi] = best_node
        node_to_v[node].remove(v)
        node_to_v[best_node].add(v)
        capacity[node] = capacity[node] - 1
        capacity[best_node] = capacity[best_node] + 1
    
if len(sys.argv) < 3:
    print("Usage: python partition.py [vertex_file] [edges_file]")
    exit()

read_vertices(sys.argv[1])
read_edges(sys.argv[2])
# print_data_structures()
# stats()
print_graph('test_graph')
partition_a ()
print_graph('test_graph_2')
