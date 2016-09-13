#!/usr/bin/env python
import argparse
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
parser.add_argument("key", type=int, help="object key")
parser.add_argument("value", type=str, help="object value to write")
args = parser.parse_args()

cl = StoreClient(store_addr=(args.host, args.port))

resp = cl.req(w_key=args.key, w_value=args.value)
assert(resp.type == TYPE_RES)
print status_to_string[resp.status]
