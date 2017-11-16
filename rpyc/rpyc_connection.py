import rpyc
import sys

class ClientService(rpyc.Service):

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
    t = ThreadedServer(ServerService, port=portNum)
    t.start()


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print("Usage: python rpyc_client.py [client_port_num] [server_port_num] [vertex_to_move_from_client_to_server]")
        exit()

    clientPort = int(sys.argv[1])
    serverPortList = sys.argv[2:-1]#int(sys.argv[2])
    # The vertex to move should be the last argument
    vertex = int(sys.argv[-1])

    # run client code (might need to do for loop so we can do multiple
    # connections to multiple nodes) TODO
    for serverPort in serverPortList:
        proxy = rpyc.connect('localhost', int(serverPort), service=ClientService)#, config={'allow_public_attrs': True})

        proxy.root.add_vertex(serverPort, clientPort, vertex)

    # run server code
    server_setup(clientPort)

