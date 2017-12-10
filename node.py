import socket
import sys
from psocket import psocket
from time import sleep
import pickle
import threading
import os
import random
import time
from termcolor import colored
import ast

#################### NODE STRUCTURES ####################

# message store
message_buf = []
accept_replies = []
accept_replies_nodes = []
prepare_replies = []

# globals
my_node = -1
direct = ""
config = None
my_port = -1
nodes = None
node_to_port = None

v_set = None
v_to_node = None
v_to_v = None
node_to_capacity = None

#################### PAXOS HELPERS ####################

class Proposal:
    def __init__ (self, instance = -1, round_num = -1,
                  node_id = -1, txn = ""):
        self.instance = instance
        self.round_num = round_num
        self.node_id = node_id
        self.txn = txn
        
    def __str__ (self):
        return (str(self.instance) + "|" + str(self.round_num) + "|" +
                str(self.node_id) + "|" + self.txn)

    def from_string (self, proposal_str):
        self.instance = int(proposal_str.split('|')[0])
        self.round_num = int(proposal_str.split('|')[1])
        self.node_id = int(proposal_str.split('|')[2])
        self.txn = proposal_str.split('|')[3]

    def __eq__ (self, p2):
        return (self.instance == p2.instance and
                self.round_num == p2.round_num and
                self.node_id == p2.node_id)

    def __gt__ (self, p2):
        return (self.round_num > p2.round_num or
                (self.round_num == p2.round_num and
                 self.node_id > p2.node_id))

    def __ge__ (self, p2):
        return self == p2 or self > p2

    def update_transaction(self, txn):
        self.txn = txn

#me, nodes_set, node_to_v_map, edges_list) paxos globals
cur_instance = -1
proposer_proposal = Proposal()
max_round = 1
cur_min_proposal = None

cur_accepted_proposal = Proposal()
highest_accepted_proposal = None

# locks
proposer_sema = {}
message_buf_lock = threading.Lock()
worker_lock = threading.Lock()

# message helpers

def add_prepare_reply (proposal):
    prepare_replies.append(proposal)

def num_prepare_replies ():
    return len(prepare_replies)

def check_prepare_replies_nodes (node1, node2):
    '''
        Check that the prepare replies came from both nodes
        at least
    '''
    found_node_1 = False
    found_node_2 = False
    for reply in prepare_replies:
        if reply.node_id == node1:
            found_node_1 = True
        elif reply.node_id == node2:
            found_node_2 = True

        print("reply: " + str(reply))

    return (found_node_1 and found_node_2)

def clear_prepare_replies ():
    global prepare_replies
    prepare_replies = []

def clear_accept_replies ():
    global accept_replies
    accept_replies = []

def clear_accept_replies_nodes ():
    global accept_replies_nodes
    accept_replies_nodes = []
    
def add_accept_reply (p):
    global accept_replies
    accept_replies.append(p)

def add_accept_replies_nodes (n):
    global accept_replies_nodes
    accept_replies_nodes.append(n)

def num_accept_replies ():
    return len(accept_replies)

def check_accept_replies_nodes (node1, node2):
    '''
        Check that the accept replies came from both nodes
        at least
    '''
    print("we want to find: " + str(node1) + " and " + str(node2))
    found_node_1 = False
    found_node_2 = False
    for node in accept_replies_nodes:
        if int(node) == node1:
            found_node_1 = True
        elif int(node) == node2:
            found_node_2 = True

        print("reply: " + str(node))

    return (found_node_1 and found_node_2)

def send_to (send_data, node_id):
    if node_id == my_node:
        add_message(0, send_data)
    else:
        try:
            sock = psocket(blocking = True)
            sock.pconnect('localhost', node_to_port[node_id])
            sock.psend(send_data)
            sock.close()
        except:
            return

def broadcast (data):
    for n in nodes:
        send_to(data, n)
            
def add_message (index, data):
    message_buf_lock.acquire()
    message_buf.insert(index,data)
    message_buf_lock.release()
    
def get_message ():
    message_buf_lock.acquire()
    if len(message_buf) > 0:
        data = message_buf.pop()
    else:
        data = ""
    message_buf_lock.release()
    return data

#################### MESSAGE HELPERS ####################

# message tags
PREPARE_TAG = "<P>"
ACCEPT_TAG = "<A>"
CHOSEN_TAG = "<C>"
PREPARE_REPLY_TAG = "<PR>"
ACCEPT_REPLY_TAG = "<AR>"

# chosen message helpers

def chosen_message (proposal):
    return CHOSEN_TAG + str(proposal)

def is_chosen (data):
    return CHOSEN_TAG == data[0:len(CHOSEN_TAG)]

def parse_chosen (data):
    return data[len(CHOSEN_TAG):]

# prepare message helpers

def prepare_message (proposal):
    return PREPARE_TAG + str(proposal)

def is_prepare (data):
    return PREPARE_TAG == data[0:len(PREPARE_TAG)]

def parse_prepare (data):
    return data[len(PREPARE_TAG):]
    
# prepare reply message helpers

def prepare_reply_message (proposal, cur_accepted_proposal, node_id):
    return (PREPARE_REPLY_TAG + str(proposal) + "#" +
            str(cur_accepted_proposal) + "#" + str(node_id))

def is_prepare_reply (data):
    return PREPARE_REPLY_TAG == data[0:len(PREPARE_REPLY_TAG)]

def parse_prepare_reply (data):
    ret = data[len(PREPARE_REPLY_TAG):].split('#')    
    return ret[0], ret[1], ret[2]
    
# accept message helpers

def accept_message (proposal):
    return ACCEPT_TAG + str(proposal)

def is_accept (data):
    return ACCEPT_TAG == data[0:len(ACCEPT_TAG)]

def parse_accept (data):
    return data[len(ACCEPT_TAG):]

# accept reply message helpers

def accept_reply_message (proposal, cur_min_proposal, node_id):
    return (ACCEPT_REPLY_TAG + str(proposal) + "#" +
            str(cur_min_proposal) + "#" + str(node_id))

def is_accept_reply (data):
    return ACCEPT_REPLY_TAG == data[0:len(ACCEPT_REPLY_TAG)]

def parse_accept_reply (data):
    ret = data[len(ACCEPT_REPLY_TAG):].split('#')
    return ret[0], ret[1], ret[2]

#################### TRANSACTION HELPER ####################

VERTEXTAG = "<VERTEX>"
# This lists the vertices that are connected to the above vertex
VERTEXLISTTAG = "<VERTEXEDGE>"
VERTEXNODETAG = "<VERTEXNODE>"
OLDNODETAG = "<OLDNODE>"
NEWNODETAG = "<NEWNODE>"

transactions = {}
t_lock = threading.Lock()

def add_transaction (p):
    instance = p.instance
    node_id = p.node_id
    txn = p.txn
    t_lock.acquire()
    if instance not in transactions:
        transactions[instance] = (node_id, txn)
    t_lock.release()

def get_transaction (instance):
    t_lock.acquire()
    node_id = transactions[instance][0]
    txn = transactions[instance][1]
    t_lock.release()
    return node_id, txn

def chosen (instance):
    t_lock.acquire()
    if instance in transactions:
        t_lock.release()
        return 1
    else:
        t_lock.release()
        return 0

def out_in (v, v_to_node_map, v_to_v_map):
    node = v_to_node_map[v]
    out_n = set()
    in_n = set()
    for vi in v_to_v_map[v]:
        if v_to_node_map[vi] == node:
            in_n.add(vi)
        else:
            out_n.add(vi)
    return out_n, in_n

def suggest_transaction (this_node, vertex_set, this_v_to_v, this_v_to_node, this_node_to_capacity):

    # return "TXN_" + str(my_node)
    nodes = this_node_to_capacity.keys()
    txn_msg = "NONE"
    # print("suggest_transaction:")
    # print("this_node: " + str(this_node))
    # print("vertex_set: " + str(vertex_set))
    # print("this_v_to_v: " + str(this_v_to_v))
    # print("this_v_to_node: " + str(this_v_to_node))
    # print("this_node_to_capacity: " + str(this_node_to_capacity))
    # need to make sure we have at least one vertex
    # to potentially transfer to another node
    if len(vertex_set) > 0:
        v = random.choice(list(vertex_set))

        # out and in neighbors
        out_n, in_n = out_in(v, this_v_to_node, this_v_to_v)
        # out edges by node
        out_counts = {}
        for n in nodes:
            out_counts[n] = 0
        for vi in out_n:
            out_node = this_v_to_node[vi]
            out_counts[out_node] = out_counts[out_node] + 1
        best_node = max(out_counts.iterkeys(),
                        key=lambda k: out_counts[k])
        # diff is num_outedges - num_inedges
        diff = out_counts[best_node] - len(in_n)

        # check that the node we want to send this vertex to has capacity
        if diff > 0 and this_node_to_capacity[best_node] > 0:
            # send neighbors and corresponding nodes
            neighbors = this_v_to_v[v]
            neighbor_nodes = [this_v_to_node[i] for i in neighbors]
            txn_msg = VERTEXTAG + str(v) + \
                      VERTEXLISTTAG + str(list(neighbors)) + \
                      VERTEXNODETAG + str(list(neighbor_nodes)) + \
                      OLDNODETAG + str(this_node) + \
                      NEWNODETAG + str(best_node)        
    return txn_msg

def get_nodes_from_transaction(txn):

    if VERTEXTAG not in txn or \
       VERTEXLISTTAG not in txn or \
       VERTEXNODETAG not in txn or \
       OLDNODETAG not in txn or \
       NEWNODETAG not in txn:
        return None

    # Get the sender node id
    sender_first = txn.find(OLDNODETAG) + len(OLDNODETAG)
    sender_last = txn.find(NEWNODETAG)
    sender_node = int(txn[sender_first:sender_last])

    # Get the recipient node id
    recv_first = txn.find(NEWNODETAG) + len(NEWNODETAG)
    recv_node = int(txn[recv_first:])

    return (sender_node, recv_node)     

def parse_transaction(txn):

    if VERTEXTAG not in txn or \
       VERTEXLISTTAG not in txn or \
       VERTEXNODETAG not in txn or \
       OLDNODETAG not in txn or \
       NEWNODETAG not in txn:
        #print("something terrible happened.....")
        return None
    
    # Get the vertex id
    vertex_first = txn.find(VERTEXTAG) + len(VERTEXTAG)        
    vertex_last = txn.find(VERTEXLISTTAG)
    vertex_id = int(txn[vertex_first:vertex_last])

    # Get the vertices that were connected to the above vertex
    vertex_list_first = txn.find(VERTEXLISTTAG) + len(VERTEXLISTTAG)
    vertex_list_last = txn.find(VERTEXNODETAG)
    vertex_list_str = txn[vertex_list_first:vertex_list_last]
    print("vertex_list: " + vertex_list_str)
    vertex_list = list(ast.literal_eval(vertex_list_str))

    # Get the nodes that those vertices are on
    vertex_node_list_first = txn.find(VERTEXNODETAG) + \
                             len(VERTEXNODETAG)
    vertex_node_list_last = txn.find(OLDNODETAG)
    vertex_node_list_str = txn[vertex_node_list_first:vertex_node_list_last]
    print("vertex_node_list: " + vertex_node_list_str)
    vertex_node_list = list(ast.literal_eval(vertex_node_list_str))
    
    # Get the sender node id
    sender_first = txn.find(OLDNODETAG) + len(OLDNODETAG)
    sender_last = txn.find(NEWNODETAG)
    sender_node = int(txn[sender_first:sender_last])

    # Get the recipient node id
    recv_first = txn.find(NEWNODETAG) + len(NEWNODETAG)
    recv_node = int(txn[recv_first:])

    return (vertex_id, vertex_list, vertex_node_list, sender_node, recv_node) 

def log_transaction(this_node, vertex_set, this_v_to_v, this_v_to_node, this_node_to_capacity):
    directory = "node_" + str(this_node) + "/"

    v_set_f = open(directory + "v_set.p", "wb")
    pickle.dump(vertex_set, v_set_f)
    v_set_f.close()

    # select only vertices on this node
    v_to_v_f = open(directory + "v_to_v.p", "wb")
    pickle.dump(this_v_to_v, v_to_v_f)
    v_to_v_f.close()

    # store v to node only for vertices node knows about
    v_to_node_f = open(direct + "v_to_node.p", "wb")
    pickle.dump(this_v_to_node, v_to_node_f)
    v_to_node_f.close()

    # keep track of the capacities at all the nodes
    capacity_f = open(direct + "capacity.p", "wb")
    pickle.dump(this_node_to_capacity, capacity_f)
    capacity_f.close()

def execute_transaction (txn, this_node, vertex_set, this_v_to_v,
                         this_v_to_node, this_node_to_capacity):
    if txn == "NONE":
        return (vertex_set, this_v_to_node, this_node_to_capacity)
    
    res = parse_transaction(txn)

    if res is None:
        return (vertex_set, this_v_to_node, this_node_to_capacity)

    (v, edge_list, vertex_node_list, snd_node, recv_node) = res

    # Make the updates to the local data structures
    if snd_node == this_node:
        vertex_set.remove(v) #note we are still keeping stale data for
        #its neighbors that we didn't remove
    elif recv_node == this_node:
        vertex_set.add(v)

    this_v_to_v[v] = edge_list
    this_v_to_node[v] = recv_node
    this_node_to_capacity[snd_node] += 1
    this_node_to_capacity[recv_node] -= 1
    for i in range(0,len(edge_list)):
        if edge_list[i] in this_v_to_node:
            if this_v_to_node[edge_list[i]] != vertex_node_list[i]:
                print "Somethings fishy"
        this_v_to_node[edge_list[i]] = vertex_node_list[i]

    log_transaction(this_node, vertex_set, this_v_to_v, this_v_to_node, this_node_to_capacity)

    print "Executed: " + txn

    return (vertex_set, this_v_to_node, this_node_to_capacity)

#################### PRINT HELPER ####################

def print_run(x):
    print x

def print_proposer (x):
    return
    #print colored("\t" + x, "blue")

def print_acceptor (x):
    return
    #print colored("\t\t" + x, "cyan")

def print_graph_structures():
    global my_node, v_set, v_to_node, v_to_v, node_to_capacity
    print("my node: " + str(my_node))
    print("vertex set: " + str(v_set))
    print("vertex to node map: " + str(v_to_node))
    print("vertex to vertex list map: " + str(v_to_v))
    print("node to capacity map: " + str(node_to_capacity))

#################### COMMAND CONTROL ####################
    
def server ():     
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', my_port))
    server.listen(len(nodes))
    while True:
        try:
            sock, address = server.accept()
            psock = psocket(sock, blocking = True)
            data = psock.precv()
            add_message(0, data)
            psock.close()
        except:
            sleep(.1)
            continue

def refresh ():
    global proposer_proposal, max_round
    global cur_min_proposal, cur_accepted_proposal
    global highest_accepted_proposal
    clear_prepare_replies()
    clear_accept_replies()
    proposer_proposal = Proposal()
    max_round = 1
    cur_min_proposal = None
    cur_accepted_proposal = Proposal()
    highest_accepted_proposal = None
        
def worker ():
    global proposer_proposal, max_round
    global cur_min_proposal, cur_accepted_proposal
    global highest_accepted_proposal
    global cur_instance

    #local_proposer_proposal = proposer_proposal
    #local_max_round = max_round
    #local_cur_min_proposal = cur_min_proposal
    #local_cur_accepted_proposal = cur_accepted_proposal
    #local_highest_accepted_proposal = highest_accepted_proposal
    #local_cur_instance = cur_instance 
    while True:
        worker_lock.acquire()
        data = get_message()

        if is_chosen(data):
            chosen_proposal = Proposal()
            chosen_proposal.from_string(parse_chosen(data))
            # push off future instance until we decide this one
            if chosen_proposal.instance > cur_instance:
                add_message(0, data)
            else:
                add_transaction(chosen_proposal)
                proposer_sema[cur_instance].release()
                print_proposer("RCVD CHOSEN MESSAGE")

        # prepare message received by acceptor
        if is_prepare(data):
            proposal = Proposal()
            proposal.from_string(parse_prepare(data))
            # push off future instance until we decide this one
            if proposal.instance > cur_instance:
                add_message(0, data)
            else:
                print_acceptor("PREPARE_MSG: " + str(proposal))
            if proposal.instance == cur_instance:
                if (cur_min_proposal is None or
                    proposal > cur_min_proposal):
                    cur_min_proposal = proposal
                    send_data = prepare_reply_message(proposal,
                                                      cur_accepted_proposal,
                                                      my_node)
                    send_to(send_data, proposal.node_id)
                else:
                    print_acceptor("MSG IGNORED")
            
        elif is_prepare_reply(data):
            ret = parse_prepare_reply(data)
            # proposal that caused this reply
            sender = Proposal()
            sender.from_string(ret[0])
            # accepted proposal from acceptor                      
            accepted = Proposal()
            accepted.from_string(ret[1])
            # node id who sent the reply
            acceptor_id = ret[2]
            # ignore old messages
            if sender == proposer_proposal:
                print_proposer("PREPARE_REPLY Node #" +
                               str(acceptor_id) + " :" + str(accepted))
                add_prepare_reply(accepted)
                if num_prepare_replies() == len(nodes)/2 + 1:
                    print_proposer("RCVD PREPARE MAJORITY")
                    highest_accepted_proposal = max(prepare_replies)

                    start = time.time()

                    this_txn = highest_accepted_proposal.txn
                    if (type(this_txn).__name__ == "str"):
                        print("tada: " + this_txn)
                        res = get_nodes_from_transaction(this_txn)
                        if res != None:
                            (sndr_node, recvr_node) = res
                            print(check_prepare_replies_nodes (sndr_node, recvr_node))
                    
                    if highest_accepted_proposal.round_num != -1:
                        proposer_proposal.txn = highest_accepted_proposal.txn
                    clear_prepare_replies()
                    proposer_sema[proposer_instance].release()
                    
        elif is_accept(data):
            proposal = Proposal()
            proposal.from_string(parse_accept(data))
            if proposal.instance > cur_instance:
                add_message(0, data)
            else:
                print_acceptor("ACCEPT_MSG: " + str(proposal))
            if proposal.instance == cur_instance:
                if (cur_min_proposal is None or proposal >=
                    cur_min_proposal):
                    cur_accepted_proposal = proposal
                    cur_min_proposal = proposal
                else:
                    print_acceptor("Proposal too low")
                send_data = accept_reply_message(proposal,
                                                 cur_min_proposal,
                                                 my_node)
                print("Sending: " + str(send_data) + " from node: " + str(my_node))
                send_to(send_data, proposal.node_id)

        elif is_accept_reply (data):
            ret = parse_accept_reply(data)
            # proposal that caused this reply
            sender = Proposal()
            sender.from_string(ret[0])
            # accepted proposal from acceptor                      
            min_proposal = Proposal()
            min_proposal.from_string(ret[1])
            # node id who sent the reply
            acceptor_id = ret[2]
            # ignore old messages
            if sender == proposer_proposal:
                print_proposer("ACCEPT_REPLY RCVD NODE #" +
                               str(acceptor_id) + ": " +
                               str(min_proposal))
                add_accept_reply(min_proposal)
                add_accept_replies_nodes(acceptor_id)
                if num_accept_replies() == len(nodes)/2 + 1:
                    print_proposer("RCVD ACCEPT MAJORITY")

                    #start = time.time()

                    this_txn = proposer_proposal.txn
                    if (type(this_txn).__name__ == "str"):
                        res = get_nodes_from_transaction(this_txn)
                        if res != None:
                            (sndr_node, recvr_node) = res
                            if check_accept_replies_nodes (sndr_node, recvr_node) is False:
                                proposer_proposal.txn = "NONE"

                    if max(accept_replies) > proposer_proposal:
                        print_proposer("REJECTED")
                        proposer_proposal.round_num = max(accept_replies).round_num + 1
                    else:
                        print_proposer("VALUE CHOSEN.")

                        print("lakers: " + str(proposer_proposal))
                        add_transaction(proposer_proposal)
                        broadcast(chosen_message(proposer_proposal))
                    clear_accept_replies()
                    proposer_sema[proposer_instance].release()
        worker_lock.release()

# proposes txn for one instance of paxos
def proposer (instance, txn):
    global proposer_instance, proposer_proposal
    proposer_instance = instance
    proposer_proposal = Proposal(instance, max_round, my_node, txn)        
    while not chosen(instance):
        print_proposer("SENDING PREPARE: " +
                       str(proposer_proposal))
        broadcast(prepare_message(proposer_proposal))
        proposer_sema[instance].acquire()
        if chosen(instance): return
        print_proposer("SENDING ACCEPT: " + str(proposer_proposal))
        broadcast(accept_message(proposer_proposal))
        proposer_sema[instance].acquire()
    print_proposer("PROPOSER FINISHED INSTANCE: " + str(instance))
    return

def setup ():
    global my_node, direct, config, my_port, nodes, node_to_port, \
           v_set, v_to_node, v_to_v, node_to_capacity
    my_node = int(sys.argv[1])
    directory = "node_" + str(my_node) + "/"

    config_f = open(directory + "config.p", "rb")
    config = pickle.load(config_f)
    config_f.close()

    my_port = config[0]
    nodes = config[1]
    node_to_port_f = open(directory + "node_to_port.p", "rb")
    node_to_port = pickle.load(node_to_port_f)
    node_to_port_f.close()

    v_set_f = open(directory + "v_set.p", "rb")
    v_set = pickle.load(v_set_f)
    v_set_f.close()

    v_to_node_f = open(directory + "v_to_node.p", "rb")
    v_to_node = pickle.load(v_to_node_f)
    v_to_node_f.close() 

    v_to_v_f = open(directory + "v_to_v.p", "rb")
    v_to_v = pickle.load(v_to_v_f)
    v_to_v_f.close()

    node_to_capacity_f = open(directory + "capacity.p", "rb")
    node_to_capacity = pickle.load(node_to_capacity_f)
    node_to_capacity_f.close()

def get_wait_time():
    txn_count = 0
    t_lock.acquire()
    for i in transactions:
        if transactions[i][0] == my_node:
            txn_count +=1
    if len(transactions) == 0:
        t_lock.release()
        return 0
    else:
        t_lock.release()
        return float(txn_count)/len(transactions)        
    
def run ():

    global cur_instance, my_node, v_set, v_to_v, v_to_node, node_to_capacity  
    worker_lock.acquire()

    # worker reads messages (currently locked)
    m = threading.Thread(target=worker)
    m.daemon = True
    m.start()

    cur_instance = 1
    
    for i in range(0,10):
        print_run("STARTING PAXOS #" + str(cur_instance))
        if not chosen(cur_instance):
            txn = suggest_transaction(my_node, v_set, v_to_v, v_to_node, node_to_capacity)
            #txn = suggest_transaction()
            proposer_sema[cur_instance] = threading.Semaphore(0)
            # start worker for this instance
            worker_lock.release()
            # start proposer
            wait = get_wait_time()
            print ("Waiting " + str(wait) + " before proposing")
            sleep(wait)
            p = threading.Thread(target=proposer,
                                 args=(cur_instance, txn))
            p.daemon = True
            p.start()
            # stop proposer
            p.join()
            # stop worker
            worker_lock.acquire()
            # refresh paxos state
            refresh()
        node_id, txn = get_transaction(cur_instance)
        print "Executing: " + txn + " from Node #" + str(node_id)
        #print("Before:")
        #print_graph_structures()
        (v_set, v_to_node, node_to_capacity) = execute_transaction (txn, my_node, v_set, v_to_v, v_to_node, node_to_capacity)
        #print("After:")
        #print_graph_structures()
        cur_instance += 1
    print "done."

print "Starting"
setup()
# start accepting messages
s = threading.Thread(target=server)
s.daemon = True
s.start()
# sleep until all nodes are up
sleep(2*(len(nodes)))
run()
