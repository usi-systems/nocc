#!/usr/bin/env python
import argparse
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
parser.add_argument("key", type=int, help="object key")
args = parser.parse_args()

cl = StoreClient(store_addr=(args.host, args.port))

resp = cl.req(r_key=args.key)
assert(resp.type == TYPE_RES)
if resp.status != STATUS_OK:
    print status_to_string[resp.status]
else:
    print resp.value.rstrip('\0')
