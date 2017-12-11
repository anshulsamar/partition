import rpyc
import sys
import thread
from rpyc.utils.server import ThreadedServer

'''
  Exposed service provided by the server
'''
class ServerService(rpyc.Service):

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
    t = ThreadedServer(ServerService, port=portNum)
    t.start()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python rpyc_server.py [server_port_num]")
        exit()
    
    server_setup(int(sys.argv[1]))

    '''
    for idx, serverNum in enumerate(sys.argv[1:]):
        print idx, serverNum
        thread.start_new_thread(server_setup, (int(serverNum),))
    '''
