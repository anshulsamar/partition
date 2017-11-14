import rpyc

class ServerService(rpyc.Service):

    def exposed_add_vertex(self, serverPort, vertexNum):
      serverFile = open(str(serverPort) + "vertices.txt", "a")
      serverFile.write(str(vertexNum) + "\n")
      serverFile.close()


class ClientService(rpyc.Service):

    def exposed_remove_vertex(self, clientPort, vertexNum):
      clientFileName = str(clientPort) + "vertices.txt"
      clientFile = open(clientFileName, "r")
      lines = clientFile.readlines()
      lines.close()
      
      clientFile = open(clientFileName, "w")
      for line in lines:
        if int(line) != vertexNum:
          clientFile.write(line)
      clientFile.close()

from rpyc.utils.server import ThreadedServer
t = ThreadedServer(ServerService, port = 20000)
#t.start()
#t.close()

proxy = rpyc.connect('localhost', 10000, service=ClientService, config={'allow_public_attrs': True})

proxy.root.add_vertex(10000, 2)

