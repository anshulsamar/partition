import rpyc

class ServerService(rpyc.Service):
    '''
    def exposed_line_counter(self, fileobj, function):
        for linenum, line in enumerate(fileobj.readlines()):
            function(line)
        print self._conn.root.hi()
        return linenum + 1
    '''

    def exposed_add_vertex(self, serverPort, vertexNum):
      serverFile = open(str(serverPort) + "vertices.txt", "a")
      serverFile.write(str(vertexNum) + "\n")
      serverFile.close()

from rpyc.utils.server import ThreadedServer
t = ThreadedServer(ServerService, port = 10000)
t.start()
