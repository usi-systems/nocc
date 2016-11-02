#!/usr/bin/env python
import argparse
from gotthard import *

def auto_int(x):
    return int(x, 0)

parser = argparse.ArgumentParser()
parser.add_argument("r_key", type=auto_int, help="read key")
parser.add_argument("r_value", type=str, help="read value")
parser.add_argument("w_key", type=auto_int, help="write key")
parser.add_argument("w_value", type=str, help="write value")
parser.add_argument('-s', "--host", type=str, help="server hostname", default="127.0.0.1")
parser.add_argument('-p', "--port", type=int, help="server port", default=9999)
args = parser.parse_args()

cl = GotthardClient(store_addr=(args.host, args.port))

R, W, RB = GotthardClient.R, GotthardClient.W, GotthardClient.RB

with GotthardClient(store_addr=(args.host, args.port)) as cl:
    resp = cl.req([RB(args.r_key, args.r_value), W(args.w_key, args.w_value)])
    assert(resp.flags.type == TYPE_RES)
    if resp.status != STATUS_OK:
        print "%d: %s" % (args.r_key, resp.op(k=args.r_key).value.rstrip('\0'))
    print status_to_string[resp.status]
