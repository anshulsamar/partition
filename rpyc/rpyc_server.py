import rpyc
import sys
from rpyc.utils.server import ThreadedServer

'''
  Exposed service provided by the server
'''
class ServerService(rpyc.Service):

    def exposed_add_vertex(self, serverPort, clientPort, vertexNum):
      serverFile = open(str(serverPort) + "vertices.txt", "a")
      serverFile.write(str(vertexNum) + "\n")
      serverFile.close()

      self._conn.root.remove_vertex(clientPort, vertexNum)

if len(sys.argv) < 2:
    print("Usage: python rpyc_server.py [server_port_num]")
    exit()

portNum = int(sys.argv[1])

t = ThreadedServer(ServerService, port = portNum)
t.start()
