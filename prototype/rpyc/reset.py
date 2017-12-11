# Resets the vertex text files

import sys

def write_vertices(filename, vertices):
    f = open(filename, "w")
    for i in vertices:
        f.write(str(i) + "\n")
    f.close()

if len(sys.argv) > 1:
    for port in sys.argv[1:]:
        if int(port) == 10001:
            write_vertices("10001vertices.txt", range(5))
        elif int(port) == 10002:
            write_vertices("10002vertices.txt", range(10, 15))
        elif int(port) == 10003:
            write_vertices("10003vertices.txt", range(100, 105)) 
