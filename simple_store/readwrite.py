#!/usr/bin/env python
import argparse
from gotthard import *

def auto_int(x):
    return int(x, 0)

parser = argparse.ArgumentParser()
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
parser.add_argument("r_key", type=auto_int, help="read key")
parser.add_argument("r_value", type=str, help="read value")
parser.add_argument("w_key", type=auto_int, help="write key")
parser.add_argument("w_value", type=str, help="write value")
args = parser.parse_args()

cl = StoreClient(store_addr=(args.host, args.port))

r, w = StoreClient.r, StoreClient.w

with StoreClient(store_addr=(args.host, args.port)) as cl:
    resp = cl.req([r(args.r_key, args.r_value), w(args.w_key, args.w_value)])
    assert(resp.flags.type == TYPE_RES)
    if resp.status != STATUS_OK:
        print "%d: %s" % (args.r_key, resp.op(k=args.r_key).value.rstrip('\0'))
    print status_to_string[resp.status]
