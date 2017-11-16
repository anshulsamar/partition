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

if len(sys.argv) < 3:
    print("Usage: python rpyc_client.py [client_port_num] [server_port_num] [vertex_to_move_from_client_to_server]")
    exit()

clientPort = int(sys.argv[1])
serverPort = int(sys.argv[2])
vertex = int(sys.argv[3])

proxy = rpyc.connect('localhost', serverPort, service=ClientService)#, config={'allow_public_attrs': True})

proxy.root.add_vertex(serverPort, clientPort, vertex)

