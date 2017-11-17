# Reads in vertex list. Format: <vertex_id>. Reads in
# undirected edge list. Format: <vertex_id>,<vertex_id>
# Randomly assigns vertices to N nodes. 

import numpy as np
import random
#from graphviz import Graph
from graphfunc import print_graph
from graphfunc import GraphFeatures
import sys

# Redundant data structures for easy access
#N = 3                                   # max nodes
#nodes = set(range(0,N))                 # node identifiers
max_capacity = 10                       # max vertices/node
v_to_node = {}                          # vertex-node map
node_to_v = {}                          # node-vertex map
v_to_v = {}                             # vertex-vertex map
#edges = set()                           # edge_list
#capacity = {}                           # remaining capacity
#threshold = 0                           # partition thresh

#server_prefix = 20000                   # this is for the port number of
                                        # each server. So, for example, if
                                        # there are two servers and 
                                        # server_prefix = 20000, then the
                                        # two ports would be 20000 and 20001

# Initialize nodes
for i in GraphFeatures.nodes:
    node_to_v[i] = set()
    GraphFeatures.capacity[i] = max_capacity

print "cap: ", GraphFeatures.capacity

np.save('npy_files/capacity.npy', GraphFeatures.capacity)

# Read in vertex list and populate nodes
def read_vertices(filename):
    with open(filename, 'rb') as f:
        for line in f:
            v = int(line)
            if v not in v_to_node:
                space = [n for n in GraphFeatures.nodes if GraphFeatures.capacity[n]>0]
                if len(space) == 0:
                    print "Error: No space in nodes"
                    exit()
                node = random.choice(space)
                v_to_node[v] = node
                node_to_v[node].add(v)
                GraphFeatures.capacity[node] = GraphFeatures.capacity[node] - 1
                v_to_v[v] = set()

    # create the vertices file for each node, i.e. the vertices
    # that a node i contains
    for i in GraphFeatures.nodes:
        portnum = GraphFeatures.server_prefix + i
        node_f = open(str(portnum) + "vertices.txt", "w+")

        for v in node_to_v[i]:
            node_f.write(str(v) + "\n")

        node_f.close()

    # create a file that contains the v_to_node dictionary
    np.save('npy_files/v_to_node.npy', v_to_node)

    # create a file that contains the node_to_v dictionary
    np.save('npy_files/node_to_v.npy', node_to_v)

# Read in edge list
def read_edges(filename):
    with open(filename, 'rb') as f:
        for line in f:
            v1, v2 = line.split(',')
            v1 = int(v1)
            v2 = int(v2)
            v_to_v[v1].add(v2)
            v_to_v[v2].add(v1)
            GraphFeatures.edges.add((v1,v2))

    f.close()

    # write v_to_v dictionary to a file
    np.save('npy_files/v_to_v.npy', v_to_v)

'''
# Prints graph and nodes (based on graphviz ex)
def print_graph (fname, nodesList, edgesList, node_to_v_map):
    g = Graph('G', filename=fname, format='png')
    c = {}

    for node in nodesList:
        # Note 'cluster_' prefix required naming
        node_name = 'cluster_' + str(node)        
        c[node] = Graph(name=node_name)
        c[node].attr(style='filled')
        c[node].attr(color='lightgrey')
        c[node].node_attr.update(style='filled', color='white')
        for v in node_to_v_map[node]:
            c[node].node(str(v))                  
        c[node].attr(fontsize='8')
        c[node].attr(label=node_name)
        g.subgraph(c[node])

    for e in edgesList:
        g.edge(str(e[0]),str(e[1]))
    g.render(fname)
'''

# Print graph data structures
def print_data_structures():
    print "Vertex To Node:"
    print v_to_node
    print "Node to Vertex"
    print node_to_v
    print "Vertex to Vertex"
    print v_to_v
    print "Edges"
    print GraphFeatures.edges
    print "Capacities"
    print capacity

# Calculates basic statistics
def stats():
    for node in GraphFeatures.nodes:
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

if len(sys.argv) < 2:
    print("Usage: python partition.py [vertex_file] [edges_file]")
    exit()

read_vertices(sys.argv[1])
read_edges(sys.argv[2])
# print_data_structures()
# stats()
print "first edges: ", GraphFeatures.edges
print_graph('test_graph', GraphFeatures.nodes, GraphFeatures.edges, node_to_v)
#partition_a (nodes, node_to_v, v_to_node)
#print_graph('test_graph_2')
