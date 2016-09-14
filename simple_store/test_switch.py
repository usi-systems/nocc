#!/usr/bin/env python2

# This tests that the switch is forwarding/shortcutting correctly

import argparse
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
args = parser.parse_args()

cl = StoreClient(store_addr=(args.host, args.port))

# Populate the store with one key:
resp = cl.req(w_key=1, w_value='a')
assert(resp.status == STATUS_OK)
assert(resp.from_switch == 0) # should not have originated at the switch, but store

# Switch should return cached key:
resp = cl.req(r_key=1)
assert(resp.status == STATUS_OK)
assert(resp.from_switch == 1) # should be cached on switch
assert(resp.version > 0)
current_version = resp.version

# Switch should reject bad RW transaction
resp = cl.req(r_key=1, r_version=0, w_key=1, w_value='x')
assert(resp.status == STATUS_REJECT)
assert(resp.from_switch == 1) # switch should do the reject
assert(resp.key == 1) # and tell us current key state
assert(resp.version == current_version)
assert(resp.value.rstrip('\0') == 'a')

# Switch should not return missing key
resp = cl.req(w_key=1, null_val=1) # First, delete it
assert(resp.status == STATUS_OK)
resp = cl.req(r_key=1)             # Then, try fetching it
assert(resp.status == STATUS_NOTFOUND)
assert(resp.from_switch == 0) # should not be cached on switch
