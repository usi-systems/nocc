#!/usr/bin/env python
import sys
import json

def dumpLats(filename_in, filename_out):
    with open(filename_in, 'r') as f:
        results = json.load(f)
        lats = [lat for l in results['txn_lats'] for lat in l]
    with open(filename_out, 'w') as f:
        data = '\n'.join(map(str, lats))
        f.write(data)

for filename in sys.argv[1:]:
    print filename
    dumpLats(filename, filename + '_lats.tsv')
