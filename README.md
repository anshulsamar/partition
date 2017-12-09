# Partition 

Decentralized Partitioning of Distributed Graph. 

## todo

pull in rpyc and simulation code in prototypes folder

## Getting Started

Install graphviz

## Usage

To run the simulation:

```
python partition.py [vertex_file] [edge_file]
```

Currently this saves the original graph (test.png). It then does one
partition cycle (i.e. choose random node, pick random vector, and try to
move it). It saves the new graph (test2.png). 

Try running:

```
python partition.py test/test_vertices.txt test/test_edges.txt
```

Note there may be no vertex that moves - as the process is random.


## Acknowledgements

Thanks to David Mazieres, Jure Lescovec, Peter Bailis, Michael Chang, and
Seo Jin Park for helpful conversations. 

## Code Acknowledgemnets

 Basic threading/networking code taken from folowing tutorial:
 https://pymotw.com/2/socket/tcp.html
 https://stackoverflow.com/questions/23828264/how-to-make-a-simpl
 e-multithreaded-socket-server-in-python-that-remembers-client
 https://docs.python.org/2/howto/sockets.html#socket-howto
 https://pymotw.com/2/threading/
 Paxos based from (use similar var names, etc)
 https://ramcloud.stanford.edu/~ongaro/userstudy/paxos.pdf