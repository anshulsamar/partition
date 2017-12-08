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

#################### NODE STRUCTURES ####################

# message store
message_buf = []
accept_replies = []
prepare_replies = []

# globals
my_node = -1
direct = ""
config = None
my_port = -1
nodes = None
node_to_port = None

v_to_node = None
node_to_v = None
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
        return (str(self.instance) + "," + str(self.round_num) + "," +
                str(self.node_id) + "," + self.txn)

    def from_string (self, proposal_str):
        self.instance = int(proposal_str.split(',')[0])
        self.round_num = int(proposal_str.split(',')[1])
        self.node_id = int(proposal_str.split(',')[2])
        self.txn = proposal_str.split(',')[3]

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

# paxos globals
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

def clear_prepare_replies ():
    global prepare_replies
    prepare_replies = []

def clear_accept_replies ():
    global accept_replies
    accept_replies = []
    
def add_accept_reply (p):
    accept_replies.append(p)

def num_accept_replies ():
    return len(accept_replies)

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
    txn = transactions[instance][1]
    t_lock.release()
    return txn

def chosen (instance):
    t_lock.acquire()
    if instance in transactions:
        t_lock.release()
        return 1
    else:
        t_lock.release()
        return 0

def execute_transaction (txn):
    print "Executed: " + txn

def suggest_transaction ():
    return "TXN_" + str(my_node)

#################### PRINT HELPER ####################

def print_run(x):
    print x

def print_proposer (x):
    print colored("\t" + x, "blue")

def print_acceptor (x):
    print colored("\t\t" + x, "cyan")

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
    while True:
        worker_lock.acquire()
        data = get_message()

        if is_chosen(data):
            chosen_proposal = Proposal()
            chosen_proposal.from_string(parse_chosen(data))
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
            
        if is_prepare_reply(data):
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
                    highest_accepted_proposal = max(prepare_replies)
                    proposal.txn = highest_accepted_proposal.txn
                    proposer_sema[proposer_instance].release()
                    
        if is_accept(data):
            proposal = Proposal()
            proposal.from_string(parse_accept(data))
            if proposal.instance > cur_instance:
                add_message(0, data)
            else:
                print_acceptor("ACCEPT_MSG: " + str(proposal))
            if proposal.instance == cur_instance:
                if proposal >= cur_min_proposal:
                    cur_accepted_proposal = proposal
                    cur_min_proposal = proposal
                send_data = accept_reply_message(proposal,
                                                 cur_min_proposal,
                                                 my_node)
                send_to(send_data, proposal.node_id)

        if is_accept_reply (data):
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
                if num_accept_replies() == len(nodes)/2 + 1:
                    print_proposer("RCVD MAJORITY")
                    if max(accept_replies) > proposer_proposal:
                        print_proposer("REJECTED")
                    else:
                        print_proposer("VALUE CHOSEN.")
                        add_transaction(proposer_proposal)
                        broadcast(chosen_message(proposer_proposal))
                    proposer_sema[proposer_instance].release()
        worker_lock.release()

# proposes txn for one instance of paxos
def proposer (instance, txn):
    global proposer_instance, proposer_proposal
    proposer_instance = instance
    while not chosen(instance):
        proposer_proposal = Proposal(instance, max_round, my_node, txn)
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
    global my_node, direct, config, my_port, nodes, node_to_port
    my_node = int(sys.argv[1])
    directory = "node_" + str(my_node) + "/"
    config = pickle.load(open(directory + 'config.p','rb'))
    my_port = config[0]
    nodes = config[1]
    node_to_port = pickle.load(open(directory + 'node_to_port.p',
                                    'rb'))

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
    global cur_instance  
    worker_lock.acquire()

    # start accepting messages
    s = threading.Thread(target=server)
    s.daemon = True
    s.start()

    # worker reads messages (currently locked)
    m = threading.Thread(target=worker)
    m.daemon = True
    m.start()

    cur_instance = 1
    
    for i in range(0,2):
        print_run("STARTING PAXOS #" + str(cur_instance))
        if not chosen(cur_instance):
            txn = suggest_transaction()
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
        txn = get_transaction(cur_instance)
        execute_transaction(txn)
        cur_instance += 1
    print "done."

print "Starting"
setup()
# sleep until all nodes are up
sleep(2*(len(nodes) - my_node))
run()
