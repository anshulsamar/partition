# Partition 

Partition is a repartitioning system for distributed
graphs. Partition operates in a decentralized and dynamic
fashion, reorganizing vertices and edges across server nodes, without
the need of a master. Basic Paxos implementation in node.py. 

## Getting Started

Install graphviz

## General Usage

Create a directory to store vertex and edge files for the initial cluster
configuration. For example a vertex file looks like:

vertex.txt
//vertex_id,node_id
1,1
2,1
3,2
4,3

And an edge file looks like:

edges.txt
//endpoint_1,endpoint_2
1,2
3,4

To run pass the directory into the following command:

```
python run_script.py [#nodes] [max_capacity] [#paxos_rounds] [directory]
```

This will save images of the starting and final configurations of the
graph to the directory specified. It will output the percentage
reduction of inter-node edges after repartioning the system. It will
also create directories for individual nodes containing pickle files
describing the vertices they contain. 

## Acknowledgements

Thanks to David Mazieres, Jure Lescovec, Peter Bailis, Michael Chang, and
Seo Jin Park for helpful conversations. 


