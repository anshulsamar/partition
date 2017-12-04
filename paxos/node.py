# Basic threading/networking code taken from folowing tutorial:
# https://pymotw.com/2/socket/tcp.html
# https://stackoverflow.com/questions/23828264/how-to-make-a-simpl
# e-multithreaded-socket-server-in-python-that-remembers-client
# https://docs.python.org/2/howto/sockets.html#socket-howto
# https://pymotw.com/2/threading/
# Paxos based from (use similar var names, etc)
# https://ramcloud.stanford.edu/~ongaro/userstudy/paxos.pdf

import socket
import sys
from psocket import psocket
from time import sleep
import pickle
import threading
import os
import random
import time

# message tags
PREPARE_TAG = "<P>"
ACCEPT_TAG = "<A>"
PREPARE_REPLY_TAG = "<PR>"
ACCEPT_REPLY_TAG = "<AR>"

# replies
message_buf = []
accept_replies = []
prepare_replies = []

# globals
chosen = -1
max_round = 1
cur_val = -1
cur_min_proposal = -1
cur_accepted_proposal = -1
cur_accepted_val = -1

# locks
majority_sema = threading.Semaphore(0)
message_buf_lock = threading.Lock()

# prepare message helpers

def prepare_message (proposal_num):
    return PREPARE_TAG + str(proposal_num)

def is_prepare (data):
    return PREPARE_TAG == data[0:len(PREPARE_TAG)]

def parse_prepare (data):
    proposal_num = data[len(PREPARE_TAG):]
    return int(proposal_num)
    
# prepare reply message helpers

def prepare_reply_message (proposal_num, accepted_proposal, accepted_val):  
    tag = PREPARE_REPLY_TAG + str(proposal_num) + ","
    payload = str(accepted_proposal) + "," + str(accepted_val)
    return tag + payload

def is_prepare_reply (data):
    return PREPARE_REPLY_TAG == data[0:len(PREPARE_REPLY_TAG)]

def parse_prepare_reply (data):
    ret_val = data[len(PREPARE_REPLY_TAG):].split(',')
    proposal_num = int(ret_val[0])
    accepted_proposal = int(ret_val[1])
    accepted_val = int(ret_val[2])
    return proposal_num, accepted_proposal, accepted_val

# accept message helpers

def accept_message (proposal_num, value):
    return ACCEPT_TAG + str(proposal_num) + "," + str(value)

def is_accept (data):
    return ACCEPT_TAG == data[0:len(ACCEPT_TAG)]

def parse_accept (data):
    proposal_num, val = data[len(ACCEPT_TAG):].split(',')
    return int(proposal_num), int(val)

# accept reply message helpers

def is_accept_reply (data):
    return ACCEPT_REPLY_TAG == data[0:len(ACCEPT_REPLY_TAG)]

def accept_reply_message (proposal_num, min_proposal):
    return ACCEPT_REPLY_TAG + str(proposal_num) + "," + str(min_proposal)

def parse_accept_reply (data):
    proposal_num, min_proposal = data[len(ACCEPT_REPLY_TAG):].split(',')
    return int(proposal_num), int(min_proposal)

# other helpers (put this separately in case atomicity
# is needed later)

def add_prepare_reply(proposal_num, value):
    prepare_replies.append((proposal_num, value))

def num_prepare_replies ():
    return len(prepare_replies)

def clear_prepare_replies():
    prepare_replies = []

def clear_accept_replies():
    accept_replies()
    
def add_accept_reply(p):
    accept_replies.append(p)

def num_accept_replies ():
    return len(accept_replies)

def get_round_num(n):
    return int(str(n)[0:-1])

def get_server_id(n):
    return int(str(n)[-1])

def get_proposal_num ():
    return int(str(max_round) + str(my_node))

# message helpers

def send_to (send_data, p):
    try:
        sock = psocket(blocking = True)
        sock.pconnect('localhost', p)
        sock.psend(send_data)
        sock.close()
    except:
        return

def broadcast(data):
    for n in nodes:
        if n != my_node:
            send_to(data, node_to_port[n])

def get_message ():
    while True:
        message_buf_lock.acquire()
        if len(message_buf) > 0:
            data = message_buf.pop()
            break
        message_buf_lock.release()
    message_buf_lock.release()
    return data

# paxos helpers

def max_reply():
    max_proposal_seen = -1
    highest_accepted_proposal_value = -1
    for r in prepare_replies:
        accepted_proposal, accepted_value = r[0], r[1]
        if accepted_value != -1:
            if accepted_proposal > max_proposal_seen:
                max_proposal_seen = accepted_proposal
                highest_accepted_proposal_val = accepted_value
    return highest_accepted_proposal_value


# core

def server():     
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', my_port))
    server.listen(len(nodes))
    while True:
        try:
            sock, address = server.accept()
            sock = psocket(sock, blocking = True)
            data = sock.precv()
            message_buf_lock.acquire()
            message_buf.insert(0,data)
            message_buf_lock.release()
            sock.close()
        except:
            sleep(1)
            continue
           
def helper():
    global chosen, max_round, cur_val
    global cur_min_proposal, cur_accepted_proposal, cur_accepted_val
    while True:
        # check for message
        data = get_message()
        print "Message Received: " + str(data)

        if is_prepare(data):
            proposal_num = parse_prepare(data)
            proposer_id = get_server_id(proposal_num)
            print "Contacted by Node: " + str(proposer_id)
            if proposal_num > cur_min_proposal:
                cur_min_proposal = proposal_num
            send_data = prepare_reply_message(proposal_num,
                                              cur_accepted_proposal,
                                              cur_accepted_val)
            send_to(send_data, node_to_port[proposer_id])
            
        if is_accept(data):
            proposal_num, val = parse_accept(data)
            if proposal_num >= cur_min_proposal:
                cur_accepted_proposal = proposal_num
                cur_min_proposal = proposal_num
                cur_accepted_val =  val
            proposer_id = get_server_id(proposal_num)
            send_data = accept_reply_message(proposal_num,
                                             cur_min_proposal)
            send_to(send_data, node_to_port[proposer_id])
            
        if is_prepare_reply(data):
            ret_val = parse_prepare_reply(data)
            proposal_num = ret_val[0]
            accepted_proposal = ret_val[1]
            accepted_value = ret_val[2]
            # ignore old messages
            if proposal_num == get_proposal_num():
                add_prepare_reply(accepted_proposal, accepted_value)
                if num_prepare_replies() == len(nodes)/2:
                    highest_accepted_proposal_value = max_reply()
                    if highest_accepted_proposal_value != -1:
                        cur_val = highest_accepted_proposal_value
                        print "Received Majority Prepares: " + str(cur_val)
                    majority_sema.release()

        if is_accept_reply (data):
            proposal_num, min_proposal = parse_accept_reply (data)
            if proposal_num == get_proposal_num():
                add_accept_reply(min_proposal)
                if num_accept_replies() == len(nodes)/2:
                    print "Received Majority Acceptances, ",
                    if max(accept_replies) > proposal_num:
                        print "Rejected."
                        max_round = get_round_num(max(acceptances))
                        clear_prepare_replies()
                        clear_accept_replies()
                    else:
                        chosen = cur_val
                        print "Value Chosen: " + str(chosen)
                    majority_sema.release()

def proposer():
    global chosen, max_round, cur_val
    cur_val = random.choice([0,1])      
    while chosen == -1:      
        proposal_num = get_proposal_num()
        print "Proposal Num: " + str(proposal_num) + " Value: " + str(cur_val)
        print "Sending Prepare Messages"
        broadcast(prepare_message(proposal_num))
        majority_sema.acquire()
        print "Sending Accept Messages"
        broadcast(accept_message(proposal_num, cur_val))
        majority_sema.acquire()

my_node = int(sys.argv[1])
direct = "node_" + str(my_node) + "/"
config = pickle.load(open(direct + 'config.p','rb'))
my_port = config[0]
nodes = config[1]
node_to_port = pickle.load(open(direct + 'node_to_port.p','rb'))

if my_node == 0:
    print "Starting Proposer"
    p = threading.Thread(target=proposer)
    p.daemon = True
    p.start()

print "Starting Server"
s = threading.Thread(target=server)
s.daemon = True
s.start()

print "Starting Helper"
m = threading.Thread(target=helper)
m.daemon = True
m.start()

while True:
    sleep(.1)

