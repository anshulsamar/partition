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
def read_vertices_rand(filename, nodes_set, node_to_capacity_map,
                  v_to_node_map, node_to_v_map, v_to_v_map):
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

def read_vertices_det(filename, nodes_set, node_to_capacity_map,
                  v_to_node_map, node_to_v_map, v_to_v_map):
    with open(filename, 'rb') as f:
        for line in f:
            v = int(line.split(',')[0])
            node = int(line.split(',')[1])
            if v not in v_to_node_map:                
                v_to_node_map[v] = node
                node_to_v_map[node].add(v)
                node_to_capacity_map[node] -= 1
                v_to_v_map[v] = set()

    return (node_to_capacity_map, v_to_node_map, node_to_v_map, v_to_v_map)
    #np.save("master_v_to_node.npy", v_to_node)

def read_edges(filename, v_to_v_map, edges_list):
    with open(filename, 'rb') as f:
        for line in f:
            v1, v2 = line.split(',')
            v1 = int(v1)
            v2 = int(v2)
            v_to_v_map[v1].add(v2)
            v_to_v_map[v2].add(v1)
            edges_list.add((v1,v2))

    return (v_to_v_map, edges_list)

# Prints graph and nodes (based on graphviz ex)
def print_graph (fname, nodes_set, node_to_v_map, edges_list):
    g = Graph('G', filename=fname, format='png')
    c = {}

    for node in nodes_set:
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

    for e in edges_list:
        g.edge(str(e[0]),str(e[1]))
    g.render(fname)


# Create folders for nodes, populate data
def create_nodes(nodes_set, node_to_port_map, node_to_v_map, v_to_v_map, v_to_node_map, node_to_capacity_map):
    for node in nodes:
        direct = "node_" + str(node) + "/"
        if not os.path.exists(direct):
            os.makedirs(direct)
        port = 10000 + node
        config = [port, nodes]

        config_f = open(direct + "config.p", "wb")
        pickle.dump(config, config_f)
        config_f.close()

        node_to_port_f = open(direct + "node_to_port.p", "wb")
        pickle.dump(node_to_port_map, node_to_port_f)
        node_to_port_f.close()

        v_set_f = open(direct + "v_set.p", "wb")
        pickle.dump(node_to_v_map[node], v_set_f)
        v_set_f.close()

        # select only vertices on this node
        v_to_v_s = {}
        for v in v_to_v_map:
            if v in node_to_v_map[node]:
                v_to_v_s[v] = v_to_v_map[v]
        v_to_v_f = open(direct + "v_to_v.p", "wb")
        pickle.dump(v_to_v_s, v_to_v_f)
        v_to_v_f.close()

        # store v to node only for vertices node knows about
        v_to_node_s = {}
        for k,v in v_to_v_s.iteritems():
            if k not in v_to_node_s:
                v_to_node_s[k] = v_to_node_map[k]
            for vi in v:
                if vi not in v_to_node_s:
                    v_to_node_s[vi] = v_to_node_map[vi]
        v_to_node_f = open(direct + "v_to_node.p", "wb")
        pickle.dump(v_to_node_s, v_to_node_f)
        v_to_node_f.close()

        # keep track of the capacities at all the nodes
        capacity_f = open(direct + "capacity.p", "wb")
        pickle.dump(node_to_capacity_map, capacity_f)
        capacity_f.close()


if (len(sys.argv) < 5):
    print("USAGE: python run.py [#nodes] [capacity] [-r/-d] [dir]")
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

random_assign = (sys.argv[3] == "-r")
vertices_file = sys.argv[4] + "/vertices.txt"
edges_file = sys.argv[4] + "/edges.txt"
# Initialize nodes
for i in nodes:
    node_to_v[i] = set()
    capacity[i] = max_capacity
    node_to_port[i] = 10000 + i

clean_dirs(nodes)
if random_assign:
    (capacity, v_to_node, node_to_v, v_to_v) = read_vertices_random (vertices_file, nodes, \
                                                                     capacity, v_to_node, node_to_v, \
                                                                     v_to_v)
else:
    (capacity, v_to_node, node_to_v, v_to_v) = read_vertices_det (vertices_file, nodes, \
                                                             capacity, v_to_node, node_to_v, \
                                                             v_to_v)


   
(v_to_v, edges) = read_edges(edges_file, v_to_v, edges)


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

total_out_edges = 0
for node in nodes:
    vertices = node_to_v[node]
    if len(vertices) == 0: continue
    # total edges within node
    in_edges = 0
    # total edges leaving node
    out_edges = 0
    for v in vertices:
        out_n, in_n = out_in(v)
        v_out_node = len(out_n)
        v_in_node = len(in_n)
        # update edge counts
        in_edges = in_edges + v_in_node
        out_edges = out_edges + v_out_node
        
    #print "Node: " + str(node)
    #print "\tout edges: " + str(out_edges)
    #print "\tin edges: " + str(in_edges)        
    total_out_edges += out_edges

print float(total_out_edges)/2
print_graph(sys.argv[4] + '/starting_config', nodes, node_to_v, edges)
create_nodes(nodes, node_to_port, node_to_v, v_to_v, v_to_node, capacity)
