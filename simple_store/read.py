#!/usr/bin/env python
import argparse
from gotthard import *

def auto_int(x):
    return int(x, 0)

parser = argparse.ArgumentParser()
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
parser.add_argument("key", type=auto_int, help="object key")
args = parser.parse_args()

cl = GotthardClient(store_addr=(args.host, args.port))

R, W, RB = GotthardClient.R, GotthardClient.W, GotthardClient.RB

with GotthardClient(store_addr=(args.host, args.port)) as cl:
    resp = cl.req(R(args.key))
    assert(resp.flags.type == TYPE_RES)
    if resp.status != STATUS_OK:
        print status_to_string[resp.status]
    else:
        print resp.op(k=args.key).value.rstrip('\0')
