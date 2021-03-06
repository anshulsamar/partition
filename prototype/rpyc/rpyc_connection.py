import rpyc
import sys
import random
import numpy as np
from graphfunc import print_graph
from graphfunc import GraphFeatures
from rpyc.utils.server import ThreadedServer

class ClientService(rpyc.Service):
    print "edges: ", GraphFeatures.edges

    def exposed_remove_vertex(self, clientPort, vertexNum):
      clientFileName = str(clientPort) + "vertices.txt"
      clientFile = open(clientFileName, "r")
      lines = clientFile.readlines()
      clientFile.close()     
 
      clientFile = open(clientFileName, "w")
      for line in lines:
        if int(line) != vertexNum:
          clientFile.write(line)
      clientFile.close()

class OtherServerService(rpyc.Service):

    # Add vertex to this server's file. Note that this also
    # removes the vertex from the client's vertex file.
    def exposed_add_vertex(self, serverPort, clientPort, vertexNum):
        serverFile = open(str(serverPort) + "vertices.txt", "a")
        serverFile.write(str(vertexNum) + "\n")
        serverFile.close()

        # Remove vertex from the client's vertex file
        self._conn.root.remove_vertex(clientPort, vertexNum)

def server_setup(portNum):
    #print portNum
    t = ThreadedServer(OtherServerService, port=portNum)
    t.start()

# Returns neighbors outsidee (out) and neigbhors inside (in)
def out_in (v, v_to_node_map, v_to_v_map):
    # v_to_node_map is a int (in form of string) to int (in form of string)
    node = v_to_node_map[v]
    out_n = set()
    in_n = set()
    for vi in v_to_v_map[v]:
        if v_to_node_map[vi] == node:
            in_n.add(vi)
        else:
            out_n.add(vi)
    return out_n, in_n

# Randomly picks node. Attempts to move a random vertex
# to better node if space is available. Simple
# hueristic - if v has most neighbors in n, move to node
# n. 
def partition_a (nodes_lst, node_to_v_map, v_to_node_map):
    node = random.choice(list(nodes_lst))
    while len(node_to_v_map[node]) == 0:
      node = random.choice(list(nodes_lst))

    v = random.choice(list(node_to_v_map[node]))
    # get v_to_v_map
    v_to_v_map = np.load('npy_files/v_to_v.npy').item()
    # out and in neighbors
    out_n, in_n = out_in(v, v_to_node_map, v_to_v_map)
    # out edges by node
    out_counts = {}
    for n in nodes_lst:
        out_counts[n] = 0
    print "out_counts: ", out_counts
    for vi in out_n:
        out_node = v_to_node_map[vi]
        # makes sure we are only dealing with alive servers
        if out_node in out_counts:
            out_counts[out_node] = out_counts[out_node] + 1
    best_node = max(out_counts.iterkeys(),
                   key=lambda k: out_counts[k])
    # diff = num_outedges - num_inedges
    diff = out_counts[best_node] - len(in_n)
    # move if space in best_node
    GraphFeatures.capacity = np.load('npy_files/capacity.npy').item()
    print "capacity: ", GraphFeatures.capacity
    if diff > GraphFeatures.threshold and GraphFeatures.capacity[best_node] > 0:
        print str(v) + ": " + str(node) + " -> " + str(best_node)
        v_to_node_map[vi] = best_node
        node_to_v_map[node].remove(v)
        node_to_v_map[best_node].add(v)
        GraphFeatures.capacity[node] = GraphFeatures.capacity[node] - 1
        GraphFeatures.capacity[best_node] = GraphFeatures.capacity[best_node] + 1

        # create a file that contains the v_to_node dictionary
        np.save('npy_files/v_to_node.npy', v_to_node)

        # create a file that contains the node_to_v dictionary
        np.save('npy_files/node_to_v.npy', node_to_v)
    
        return (v, node, best_node)
    return None

if __name__ == '__main__':

    if len(sys.argv) < 3:
        print("Usage: python rpyc_client.py [client_port_num] [server_port_num]")# [vertex_to_move_from_client_to_server]")
        exit()

    clientPort = int(sys.argv[1])
    serverPortList = sys.argv[2:]#int(sys.argv[2])
    # The vertex to move should be the last argument
    #vertex = int(sys.argv[-1])

    node_to_v = np.load('npy_files/node_to_v.npy').item()
    v_to_node = np.load('npy_files/v_to_node.npy').item()

    clientPortStr = str(clientPort)

    print serverPortList

    # run client code (might need to do for loop so we can do multiple
    # connections to multiple nodes) TODO
    for serverPort in serverPortList:
        proxy = rpyc.connect('localhost', int(serverPort), service=ClientService)#, config={'allow_public_attrs': True})

        #proxy.root.add_vertex(serverPort, clientPort, vertex)

    print node_to_v
    # run partition_a and get the vertex if any
    clientServerList = [clientPort - GraphFeatures.server_prefix]
    for port in serverPortList:
      clientServerList.append(int(port) - GraphFeatures.server_prefix)

    tpl = partition_a(clientServerList, node_to_v, v_to_node)

    print "tpl: ", tpl

    if tpl != None:
        (v, clientNode, bestNode) = tpl

        print "clientNode: ", clientNode
        print "bestNode: ", bestNode
        # if somehow we got a vertex that can be transferred from this client
        # to the other servers, go for it
        if bestNode in clientServerList:
            proxy.root.add_vertex(int(bestNode) + GraphFeatures.server_prefix, clientNode + GraphFeatures.server_prefix, int(v))

    GraphFeatures.edges = np.load('npy_files/edges.npy').item()
    print "edges: ", GraphFeatures.edges
    print_graph('test_graph' + clientPortStr, GraphFeatures.nodes, GraphFeatures.edges, node_to_v)

    # run server code
    server_setup(clientPort)

