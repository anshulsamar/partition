# Partition

See master branch. This version is similar to the master, except it
survives failures up to a majority of nodes. Work on progress. We
assume message retransmission occurs.

We also assume that the node that a transaction affects has logged required data before sending an accept
and that an accept is required by that node before a transaction is
committed (not implemented). 