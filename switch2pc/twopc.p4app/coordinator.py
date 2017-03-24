#!/usr/bin/env python
import argparse
import signal
import sys
import threading
import socket
import select
import time
from Queue import Queue
from uhashring import HashRing


from minitxn import *
from minitxn import MiniTxnParser
from minitxn import writeSet, readSet, compareSet, valueSet

def log(*args): sys.stderr.write(' '.join(map(str, args)))

class Coordinator(threading.Thread):

    def __init__(self, bind_addr=('', 9000), thread_count=2, participants=[]):
        threading.Thread.__init__(self)
        self.thread_count = thread_count
        self.msg_queue = Queue()
        self.msg_handlers = []
        self.parser = MiniTxnParser()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(bind_addr)

        self.participants = participants

        self.instances = {}

        self.lock = threading.Lock()
        self.last_txn_id = 0

    def port(self):
        return self.addr()[1]

    def addr(self):
        return self.sock.getsockname()

    def connectParticipant(self, participant):
        self.participants.append(participant.addr())
        return self

    def started(self):
        pass

    def run(self):
        if self.thread_count > 1:
            self.msg_handlers = [threading.Thread(target=self._msgHandler) for _ in xrange(self.thread_count)]
            for t in self.msg_handlers: t.start()

        self.hashring = HashRing(nodes=self.participants)

        self.started()

        while True:
            readable, _, x = select.select([self.sock], [], [])
            if self.sock in readable:
                data, addr = self.sock.recvfrom(TXN_MSG_MAX_SIZE)
                if addr is None: break
                if self.thread_count > 1:
                    self.msg_queue.put((data, addr))
                else:
                    self._handleMsg(data, addr)
            else:
                break

        self.sock.close()
        for _ in self.msg_handlers: self.msg_queue.put(None)

    def stop(self):
        for s in [self.sock]:
            try:
                s.shutdown(socket.SHUT_RDWR)
            except:
                pass
        for _ in self.msg_handlers: self.msg_queue.put(None)
        for t in self.msg_handlers: t.join()


    def _msgHandler(self):
        while True:
            r = self.msg_queue.get()
            if r == None: break
            data, addr = r
            self._handleMsg(data, addr)

    def _handleMsg(self, data, addr):
            msg = self.parser.loads(data)
            if msg['msg_type'] == MSG_TYPE_REQ:
                self._handleNewTxn(msg, addr)
            elif msg['msg_type'] == MSG_TYPE_VOTE:
                self._handleVote(msg, addr)
            elif msg['msg_type'] == MSG_TYPE_COMMITTED:
                self._handleCommitted(msg, addr)
            else:
                assert False, "Unexpected message type: " + str(msg['msg_type'])

    def _handleNewTxn(self, req_msg, addr):
        with self.lock:
            self.last_txn_id += 1
            txn_id = self.last_txn_id
        node_msgs = {}
        for op_type, key, value in req_msg['ops']:
            node = self.hashring.get_node(key)
            if node not in node_msgs:
                node_msgs[node] = req_msg.copy()
                node_msgs[node]['txn_id'] = txn_id
                node_msgs[node]['msg_type'] = MSG_TYPE_PREPARE
                node_msgs[node]['ops'] = []
            node_msgs[node]['ops'].append((op_type, key, value))

        if req_msg['reset'] == 1:
            node_msgs = dict([(p, dict(req_msg, msg_type=MSG_TYPE_PREPARE, reset=1, ops=[])) for p in self.participants])

        participant_cnt = len(node_msgs)
        for node_msg in node_msgs.values():
            node_msg['participant_cnt'] = participant_cnt

        self.instances[txn_id] = dict(participants=node_msgs.keys(), result=[],
                                            cl_txn_id=req_msg['txn_id'],
                                            votes=[], commit_acks=0, client=addr, status=None, lock=threading.Lock())
        for node, node_msg in node_msgs.items():
            self.send(node_msg, node)


    def _handleVote(self, msg, addr):
        inst = self.instances[msg['txn_id']]
        with inst['lock']:
            inst['votes'].append(msg['status'] == STATUS_OK)
            inst['result'] += msg['ops']

            commit_votes = filter(lambda v: v == True, inst['votes'])
            abort_votes = filter(lambda v: v == False, inst['votes'])

            if inst['status'] is not None: # already decided COMMIT or ABORT
                return

            if len(commit_votes) == len(inst['participants']):
                commit_msg = dict(msg, msg_type=MSG_TYPE_COMMIT, status=STATUS_OK, ops=[])
                inst['status'] = STATUS_OK
                for node in inst['participants']:
                    self.send(commit_msg, node)
            elif len(abort_votes) > 0:
                abort_msg = dict(msg, msg_type=MSG_TYPE_COMMIT, status=STATUS_ABORT, ops=[])
                inst['status'] = STATUS_ABORT
                for node in inst['participants']:
                    self.send(abort_msg, node)


    def _handleCommitted(self, msg, addr):
        inst = self.instances[msg['txn_id']]
        with inst['lock']:
            inst['commit_acks'] += 1

            if len(inst['participants']) == inst['commit_acks']:
                if inst['status'] == None: # this was an early commit
                    inst['status'] = msg['status']
                res_msg = dict(msg, msg_type=MSG_TYPE_RES, status=inst['status'],
                        txn_id=inst['cl_txn_id'],
                        ops=inst['result'], participants=len(inst['participants']))
                self.send(res_msg, inst['client'])
                del self.instances[msg['txn_id']]



    def send(self, msg, addr):
        self.sock.sendto(self.parser.dumps(msg), addr)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbosity", "-v", type=int, help="set verbosity level", default=0, required=False)
    parser.add_argument("-p", "--port", type=int, help="port to bind on", required=True)
    parser.add_argument("-t", "--threads", type=int, help="number of threads", default=2)
    parser.add_argument("participant", type=lambda p: p.split(':'), nargs='+')
    args = parser.parse_args()

    participants = map(lambda (h, p): (h, int(p)), args.participant)
    co = Coordinator(bind_addr=('', args.port), participants=participants, thread_count=args.threads)
    def signal_handler(signal, frame):
        co.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    co.run()
