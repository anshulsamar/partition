import sys
import os
import pickle
from graphviz import Graph

def read_edges(filename, edges_list):
    with open(filename, 'rb') as f:
        for line in f:
            v1, v2 = line.split(',')
            v1 = int(v1)
            v2 = int(v2)
            edges_list.add((v1,v2))

    return edges_list

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

if (len(sys.argv) < 3):
    print("USAGE: python final_graph.py [#nodes] [dir]")
    exit()

N = int(sys.argv[1])                    # max nodes
nodes = set(range(0,N))                 # node identifiers

edges_file = sys.argv[2] + "/edges.txt"
edges = set()                           # edge_list

edges = read_edges(edges_file, edges)
v_to_v = {}
node_to_v = {}
v_to_node = {}
for node in nodes:
    direct = "node_" + str(node) + "/"
    if os.path.exists(direct):
        vertex_set_f = open(direct + "v_set.p", "rb")
        vertex_set = pickle.load(vertex_set_f)
        vertex_set_f.close()
        node_to_v[node] = vertex_set
        for v in vertex_set:
            v_to_node[v] = node
            v_to_v[v] = set()

for e in edges:
    v_to_v[e[0]].add(e[1])
    v_to_v[e[1]].add(e[0])

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
    total_out_edges += out_edges

print float(total_out_edges)/2
       
#print("node_to_v: " + str(node_to_v))

print_graph (sys.argv[2] + "/final_config", nodes, node_to_v, edges)
