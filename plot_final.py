import sys
import numpy as np
from graphviz import Graph

# Read in edge list
def get_edges(vertices_filename, edges_filename):
    v_to_v = {}
    edges = set()
    with open(vertices_filename, 'rb') as f:
        for line in f:
            v = int(line)
            v_to_v[v] = set()

    with open(edges_filename, 'rb') as f:
        for line in f:
            v1, v2 = line.split(',')
            v1 = int(v1)
            v2 = int(v2)
            v_to_v[v1].add(v2)
            v_to_v[v2].add(v1)
            edges.add((v1,v2))
    return edges    

# Prints graph and nodes (based on graphviz ex)
def print_graph (fname, nodes, node_to_v, edges):
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

def invert_map(m):
    new_m = {}
    for key in m:
        val = m[key]
        if val not in new_m:
            new_m[val] = [key]
        else:
            new_m[val].append(key)

    return new_m

if (len(sys.argv) < 2):
    print("USAGE: python plot_final.py [#nodes] [file1] [file2]")
    exit()


N = int(sys.argv[1])
nodes_set = set(range(0,N))
v_to_node_map = np.load("master_v_to_node.npy").item()
node_to_v_map = invert_map(v_to_node_map)
print("node_to_v map: " + str(node_to_v_map))
#read_vertices(sys.argv[2])
edges_list = get_edges(sys.argv[2], sys.argv[3])

print_graph("final_config", nodes_set, node_to_v_map, edges_list)


