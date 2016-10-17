#!/usr/bin/env python2

# Copyright 2013-present Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import subprocess
import signal
import os
import sys
import json
import time
import argparse

parser = argparse.ArgumentParser(description='Mininet demo')
parser.add_argument("--mode", "-m", choices=['read_cache', 'forward', 'early_abort', 'optimistic_abort'], type=str, default="early_abort")


args = parser.parse_args()


if __name__ == '__main__':
    max_op_cnt = 10
    t_entries = []
    if args.mode != 'forward': # i.e. both early/opti abort
        read_cache_enabled = 1 if args.mode == 'read_cache' else 0
	opti_enabled = 1 if args.mode == 'optimistic_abort' else 0
        for i in xrange(max_op_cnt):
            t_entries.append("table_add t_store_update do_store_update%d %d => %d"%(i,i+1,opti_enabled))
            t_entries.append("table_add t_req_pass1 do_check_op%d %d => %d"%(i,i+1,read_cache_enabled))
            t_entries.append("table_add t_req_fix do_req_fix%d %d =>"%(i,i+1))

    if args.mode == 'optimistic_abort':
        for i in xrange(max_op_cnt):
            t_entries.append("table_add t_opti_update do_opti_update%d %d =>"%(i,i+1))

    print '\n'.join(t_entries)


