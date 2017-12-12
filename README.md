# Partition

See master branch. This version is similar to the master, except it
survives failures of up to f nodes, where the cluster size is 2f + 1
(it takes a majority to commit a transaction). For example, nodes can
all die and start back up again and continue repartioning. Work on progress.

We also assume that the node that a transaction affects has logged required data before sending an accept
and that an accept is required by that node before a transaction is
committed (not implemented). 