#!/usr/bin/env python2

# This tests that the switch is forwarding/shortcutting correctly

import argparse
from common import *

parser = argparse.ArgumentParser()
parser.add_argument("--log", "-l", type=str, help="filename to write log to", default=None)
parser.add_argument("host", type=str, help="server hostname")
parser.add_argument("port", type=int, help="server port")
args = parser.parse_args()

cl = StoreClient(store_addr=(args.host, args.port), log_filename=args.log)

# Populate the store with one key:
resp = cl.req(w_key=1, w_value='a')
assert(resp.status == STATUS_OK)
assert(resp.from_switch == 0) # should not have originated at the switch, but store
assert(resp.key == 1)
assert(resp.value.rstrip('\0') == 'a')

# Switch should return cached key:
resp = cl.req(r_key=1)
assert(resp.status == STATUS_OK)
assert(resp.from_switch == 1) # should be cached on switch
assert(resp.key == 1)
assert(resp.value.rstrip('\0') == 'a')

# Switch should abort bad RW transaction
resp = cl.req(r_key=1, r_value='somethingelse', w_key=1, w_value='x')
assert(resp.status == STATUS_ABORT)
assert(resp.from_switch == 1) # switch should do the abort
assert(resp.key == 1) # and tell us current key state
assert(resp.value.rstrip('\0') == 'a')

# cleanup
resp = cl.req(w_key=1, w_value='')
