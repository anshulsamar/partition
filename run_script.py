import sys
import random
import subprocess
import threading

if len(sys.argv) < 5:
    print("python run_script.py [#nodes] [max_capacity] [#paxos_rounds] [directory]")
    exit(1)

num_nodes = int(sys.argv[1])
num_capacity = int(sys.argv[2])
paxos_rounds = int(sys.argv[3])
directory = sys.argv[4]

starting_edge_out = subprocess.check_output(["python","run.py",str(num_nodes),str(num_capacity),"-d",directory])

def run (node_id, paxos_rounds):
    output = subprocess.check_output(["python","node.py",str(node_id),str(paxos_rounds)])
    return

threads = []
for i in range(0,num_nodes):
    p = threading.Thread(target=run,args=(i,paxos_rounds))
    p.start()
    threads.append(p)

for i in range(0,num_nodes):
    threads[i].join()

final_edge_out = subprocess.check_output(["python","final_graph.py",str(num_nodes),directory])
print((float(starting_edge_out)-float(final_edge_out))/float(starting_edge_out))

