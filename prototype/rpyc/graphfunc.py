from graphviz import Graph

def print_graph (fname, nodesList, edgesList, node_to_v_map):
    g = Graph('G', filename=fname, format='png')
    c = {}

    print fname + "lakers"
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

class GraphFeatures:
    N = 3                                   # max nodes
    nodes = set(range(0,N))                 # node identifiers
    edges = set()                           # edge_list
    server_prefix = 20000                   # this is for the port number of
                                            # each server. So, for example, if
                                            # there are two servers and 
                                            # server_prefix = 20000, then the
                                            # two ports would be 20000 and 20001
    threshold = 0                           # partition thresh
    capacity = {}                           # remaining capacity    
     
