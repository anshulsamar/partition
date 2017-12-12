# Partition 

Partition is a repartitioning system for distributed
graphs. Partition operates in a decentralized fashion, reorganizing vertices and edges across server nodes, without
the need of a master. We operate in an asychronous setting, but assume messages are eventually delivered. The
implementation on this branch further assumes that
nodes are always live. The
implementation on /ft branch is written to survive up to f node failures, where the cluster size is 2f + 1
(it takes a majority to commit a transaction). For example, nodes can
all die and start back up again and continue
repartioning (debugging/work in progress).

See paper for applications and results. 

This project was done for CS244B (Distributed Systems) and CS224W (Analysis of Networks). 

paxos.py: node server implementation, basic paxos

setup.py: set up directories and starting config

gather.py: print final network configuration   

run_script.py: auto run repartitioning system   

exp.py: run erdos renyi, pref attachment experiments   

prototype/simulation.py: repartitioning simulation used in prototyping  

prototype/rpyc/: rpyc module used in prototyping  

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

Thanks to David Mazieres, Jure Lescovec, Peter Bailis, Seo Jin Park,
Anunay Kulshrestha, and Michael Chang for helpful conversations. 


