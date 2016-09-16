#!/usr/bin/env python
import argparse
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
parser.add_argument("r_key", type=int, help="read key")
parser.add_argument("r_value", type=int, help="read value")
parser.add_argument("w_key", type=int, help="write key")
parser.add_argument("w_value", type=str, help="write value")
args = parser.parse_args()

cl = StoreClient(store_addr=(args.host, args.port))

resp = cl.req(r_key=args.r_key, r_value=args.r_value,
              w_key=args.w_key, w_value=args.w_value)
assert(resp.type == TYPE_RES)
print status_to_string[resp.status]
