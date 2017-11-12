# Partition 

Decentralized Partitioning of Distributed Graph. 

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
