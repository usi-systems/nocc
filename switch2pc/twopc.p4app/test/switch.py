import socket
import time
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from minitxn import *

def log(*args): sys.stderr.write(' '.join(map(str, args)) + '\n')

def noResponseReceived(sock):
    try:
        sock.recvfrom(TXN_MSG_MAX_SIZE)
        return False
    except socket.timeout as e:
        return True

parser = MiniTxnParser(cl_id=1)

# The dst addr doesn't matter, since we don't care where the switch forwards
# the packet to
DST_ADDR = '10.0.1.1'

coordinator_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
coordinator_sock.bind(('', 9000))
coordinator_sock.settimeout(0.5)

participant_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
participant_sock.bind(('', 8000))
participant_sock.settimeout(0.5)

txn_id = 1

#
# One vote
#
prep_msg = dict(msg_type=MSG_TYPE_PREPARE, status=STATUS_OK, txn_id=txn_id, participant_cnt=1)
coordinator_sock.sendto(parser.dumps(prep_msg), (DST_ADDR, 8000))

vote_msg = dict(msg_type=MSG_TYPE_VOTE, status=STATUS_OK, txn_id=txn_id, participant_cnt=1)
participant_sock.sendto(parser.dumps(vote_msg), (DST_ADDR, 9000))

data, addr = participant_sock.recvfrom(TXN_MSG_MAX_SIZE)
res = parser.loads(data)
assert res['msg_type'] == MSG_TYPE_COMMIT
assert res['status'] == STATUS_OK
assert res['txn_id'] == txn_id

#
# Two votes
#
txn_id += 1
prep_msg = dict(msg_type=MSG_TYPE_PREPARE, status=STATUS_OK, txn_id=txn_id, participant_cnt=2)
coordinator_sock.sendto(parser.dumps(prep_msg), (DST_ADDR, 8000))
coordinator_sock.sendto(parser.dumps(prep_msg), (DST_ADDR, 8000))

vote_msg = dict(msg_type=MSG_TYPE_VOTE, status=STATUS_OK, txn_id=txn_id, participant_cnt=2)
participant_sock.sendto(parser.dumps(vote_msg), (DST_ADDR, 9000)) # send first vote

assert noResponseReceived(participant_sock), "should not send a response after only one vote"

participant_sock.sendto(parser.dumps(vote_msg), (DST_ADDR, 9000)) # send second vote

data, addr = participant_sock.recvfrom(TXN_MSG_MAX_SIZE)
res = parser.loads(data)
assert res['msg_type'] == MSG_TYPE_COMMIT
assert res['status'] == STATUS_OK
assert res['txn_id'] == txn_id

#
# Early abort
#
txn_id += 1
prep_msg = dict(msg_type=MSG_TYPE_PREPARE, status=STATUS_OK, txn_id=txn_id, participant_cnt=3)
coordinator_sock.sendto(parser.dumps(prep_msg), (DST_ADDR, 8000))
coordinator_sock.sendto(parser.dumps(prep_msg), (DST_ADDR, 8000))

vote_msg = dict(msg_type=MSG_TYPE_VOTE, status=STATUS_OK, txn_id=txn_id, participant_cnt=3)
participant_sock.sendto(parser.dumps(vote_msg), (DST_ADDR, 9000)) # send first vote

vote_no_msg = dict(msg_type=MSG_TYPE_VOTE, status=STATUS_ABORT, txn_id=txn_id, participant_cnt=3)
participant_sock.sendto(parser.dumps(vote_no_msg), (DST_ADDR, 9000)) # vote abort

data, addr = participant_sock.recvfrom(TXN_MSG_MAX_SIZE)
res = parser.loads(data)
assert res['msg_type'] == MSG_TYPE_COMMIT
assert res['status'] == STATUS_ABORT
assert res['txn_id'] == txn_id

participant_sock.sendto(parser.dumps(vote_msg), (DST_ADDR, 9000)) # send third vote
assert noResponseReceived(participant_sock), "should not send response after receiving third vote"

#
# Multiple ABORT votes should only trigger a single COMMIT(ABORT) message
#
txn_id += 1
prep_msg = dict(msg_type=MSG_TYPE_PREPARE, status=STATUS_OK, txn_id=txn_id, participant_cnt=2)
coordinator_sock.sendto(parser.dumps(prep_msg), (DST_ADDR, 8000))

vote_msg = dict(msg_type=MSG_TYPE_VOTE, status=STATUS_ABORT, txn_id=txn_id, participant_cnt=2)
participant_sock.sendto(parser.dumps(vote_msg), (DST_ADDR, 9000)) # send first abort

data, addr = participant_sock.recvfrom(TXN_MSG_MAX_SIZE)
res = parser.loads(data)
assert res['msg_type'] == MSG_TYPE_COMMIT
assert res['status'] == STATUS_ABORT
assert res['txn_id'] == txn_id

vote_no_msg = dict(msg_type=MSG_TYPE_VOTE, status=STATUS_ABORT, txn_id=txn_id, participant_cnt=2)
participant_sock.sendto(parser.dumps(vote_no_msg), (DST_ADDR, 9000)) # send second abort

assert noResponseReceived(participant_sock), "should not send two commit(abort) messages"


#
# Second prepare message should not reset state
#
txn_id += 1
prep_msg = dict(msg_type=MSG_TYPE_PREPARE, status=STATUS_OK, txn_id=txn_id, participant_cnt=2)
coordinator_sock.sendto(parser.dumps(prep_msg), (DST_ADDR, 8000))

vote_msg = dict(msg_type=MSG_TYPE_VOTE, status=STATUS_OK, txn_id=txn_id, participant_cnt=2)
participant_sock.sendto(parser.dumps(vote_msg), (DST_ADDR, 9000)) # send first vote

coordinator_sock.sendto(parser.dumps(prep_msg), (DST_ADDR, 8000)) # send second prepare after first vote

assert noResponseReceived(participant_sock), "second prepare message should not trigger early commit"

participant_sock.sendto(parser.dumps(vote_msg), (DST_ADDR, 9000)) # send second vote

data, addr = participant_sock.recvfrom(TXN_MSG_MAX_SIZE)
res = parser.loads(data)
assert res['msg_type'] == MSG_TYPE_COMMIT
assert res['txn_id'] == txn_id

#
# Instance state should be overwritable after 2s
#
txn_id += 1
prep_msg = dict(msg_type=MSG_TYPE_PREPARE, status=STATUS_OK, txn_id=txn_id, participant_cnt=2)
coordinator_sock.sendto(parser.dumps(prep_msg), (DST_ADDR, 8000))

vote_msg = dict(msg_type=MSG_TYPE_VOTE, status=STATUS_OK, txn_id=txn_id, participant_cnt=2)
participant_sock.sendto(parser.dumps(vote_msg), (DST_ADDR, 9000)) # send first vote

time.sleep(2.1) # wait for instance state to expire

coordinator_sock.sendto(parser.dumps(prep_msg), (DST_ADDR, 8000)) # this prep should overwrite state, resetting the votes to zero

participant_sock.sendto(parser.dumps(vote_msg), (DST_ADDR, 9000)) # send first vote again

assert noResponseReceived(participant_sock), "switch state should be reset, so it should wait for another vote before early commit"

participant_sock.sendto(parser.dumps(vote_msg), (DST_ADDR, 9000)) # send second vote

data, addr = participant_sock.recvfrom(TXN_MSG_MAX_SIZE)
res = parser.loads(data)
assert res['msg_type'] == MSG_TYPE_COMMIT
assert res['txn_id'] == txn_id
