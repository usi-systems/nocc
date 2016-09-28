#!/usr/bin/env python
import argparse
from gotthard import *

def auto_int(x):
    return int(x, 0)

parser = argparse.ArgumentParser()
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
parser.add_argument("key", type=auto_int, help="object key")
parser.add_argument("value", type=str, help="object value to write")
args = parser.parse_args()

cl = StoreClient(store_addr=(args.host, args.port))

r, w = StoreClient.r, StoreClient.w

with StoreClient(store_addr=(args.host, args.port)) as cl:
    resp = cl.req(w(args.key, args.value))
    assert(resp.flags.type == TYPE_RES)
    print status_to_string[resp.status]
