import sys
import random
import subprocess
import os
import shutil
import time

name = "pref_attachment" #"erdos_renyi" #"pref_attachment"
if os.path.exists(name + "/"):
    shutil.rmtree(name + "/")
os.makedirs(name + "")
edges_file = name + "/edges.txt"
vertices_file = name + "/vertices.txt"
num_tries = 10
#N = 5
#capacity = 7
#nodes = range(0,N)
#node_to_v = {}
#for n in nodes:
#    node_to_v[n] = set()
#num_vertices = 25
#vertices = range(0,num_vertices)
total = 0
for i in range(0,num_tries):
    N = 5
    capacity = 7
    nodes = range(0,N)
    node_to_v = {}
    for n in nodes:
        node_to_v[n] = set()
    num_vertices = 25
    vertices = range(0,num_vertices)

    if os.path.isfile(vertices_file):
        os.remove(vertices_file)
    with open(vertices_file,"wb") as f:
        file_str = ""
        for v in vertices:
            n = random.choice([ni for ni in nodes if len(node_to_v[ni]) < capacity])
            node_to_v[n].add(v)
            file_str += str(v) + "," + str(n) + "\n"
        f.write(file_str[:-1])
    if os.path.isfile(edges_file):
        os.remove(edges_file)
    if name == "erdos_renyi":
        p = .5
        with open(edges_file,"wb") as f:
            file_str = ""
            edges = set()
            for i in range(0,num_vertices):
                for j in range(0,num_vertices):
                    if i != j and (i,j) not in edges and (j,i) not in edges:
                        edges.add((i,j))
                        if random.random() < p:
                            file_str += str(i) + "," + str(j) + "\n"
            f.write(file_str[:-1])

    if name == "pref_attachment":
        edges = set()
        with open(edges_file,"wb") as f:
            p = .75
            file_str = ""
            v_to_v = {}
            for v in range(0, num_vertices):
                v_to_v[v] = []
            for v in range(0,num_vertices):
                prev_nodes = vertices[0:v]
                if len(prev_nodes) > 0:
                    if random.random() < p:
                        w = random.choice(prev_nodes)
                        v_to_v[v].append(w)
                        v_to_v[w].append(v)
                        file_str += str(v) + "," + str(w) + "\n"
                    else:
                        x = random.choice(prev_nodes)
                        if len(v_to_v[x]) > 0:
                            w = random.choice(v_to_v[x])
                            v_to_v[v].append(w)
                            v_to_v[w].append(v)
                            file_str += str(v) + "," + str(w) + "\n"
            f.write(file_str[:-1])
    #exit(1)
    percentage = subprocess.check_output(["python","run_script.py",str(N),str(capacity),"60",name+"/"])
    print(percentage)
    total += float(percentage)
    time.sleep(60)
print("Average: " + str(total/num_tries))
