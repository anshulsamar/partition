import rpyc

class MyService(rpyc.Service):
    def exposed_line_counter(self, fileobj, function):
        for linenum, line in enumerate(fileobj.readlines()):
            function(line)
        print self._conn.root.hi()
        return linenum + 1

from rpyc.utils.server import ThreadedServer
t = ThreadedServer(MyService, port = 18861)
t.start()
