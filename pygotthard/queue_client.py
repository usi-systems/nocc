#!/usr/bin/env python
import argparse
from time import sleep
from threading import Thread
from random import gauss, shuffle
import time
from gotthard import *
from gotthard_queue import GotthardQueue

class QueueClient(Thread, GotthardClient):
    def __init__(self, producer=False, consumer=False, duration=10, size=100, log=None, store_addr=None, think=None, think_var=None, resend_timeout=None):
        GotthardClient.__init__(self, store_addr=store_addr, logger=log, resend_timeout=resend_timeout)
        Thread.__init__(self)
        self.size = size
        self.think = think
        self.think_var = think_var
        self.producer = producer or not consumer
        self.duration = duration

    def run(self):
        if self.think and self.think_var: think_sigma = self.think * self.think_var

        self.op_count = 0
        self.extent = 0
        with self:
            gq = GotthardQueue(self, self.size)
            start = time.time()
            while time.time() - start < self.duration:
                if self.producer:
                    gq.push('x')
                else:
                    gq.pop()

                if gq.count > self.extent: self.extent = gq.count

                self.op_count += 1

                if self.think:
                    sleep(abs(gauss(self.think, think_sigma)) if self.think_var else self.think)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("host", type=str, help="server hostname")
    parser.add_argument("port", type=int, help="server port")
    parser.add_argument("--think", "-t", type=float, help="think time (s) between successful transactions", default=None)
    parser.add_argument("--think-var", "-v", type=float, help="variance used for generating random think time", default=0.1)
    parser.add_argument("--consumers", "-c", type=int, help="number of parallel consumers", default=1)
    parser.add_argument("--producers", "-p", type=int, help="number of parallel producers", default=1)
    parser.add_argument("--duration", "-d", type=int, help="duration in seconds", default=10)
    parser.add_argument("--size", "-s", type=int, help="number of elements in queue", default=1)
    parser.add_argument("--log", "-l", type=str, help="filename to write log to", default=None)
    args = parser.parse_args()

    logger = GotthardLogger(args.log) if args.log else None


    producers = [QueueClient(producer=True, size=args.size, log=logger, duration=args.duration, store_addr=(args.host, args.port), think=args.think, think_var=args.think_var) for _ in xrange(args.consumers)]
    consumers = [QueueClient(consumer=True, size=args.size, log=logger, duration=args.duration, store_addr=(args.host, args.port), think=args.think, think_var=args.think_var) for _ in xrange(args.consumers)]

    threads = producers + consumers
    shuffle(threads)
    for t in threads: t.start()
    for t in threads: t.join()

    print "Push count:", sum([p.op_count for p in producers])
    print "Pop count: ", sum([c.op_count for c in consumers])
    print "Extent: ", max([t.extent for t in threads])
