#!/bin/bash

# Copyright 2013-present Barefoot Networks, Inc. 
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

THIS_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

source $THIS_DIR/env.sh

P4C_BM_SCRIPT=$P4C_BM_PATH/p4c_bm/__main__.py

SWITCH_PATH=$BMV2_PATH/targets/simple_switch/simple_switch

CLI_PATH=$BMV2_PATH/tools/runtime_CLI.py

echo $P4C_BM_SCRIPT p4src/simple_router.p4 --json simple_router.json --p4-v1.1
$P4C_BM_SCRIPT p4src/simple_router.p4 --json simple_router.json --p4-v1.1
sudo python experiment.py \
    --behavioral-exe $BMV2_PATH/targets/simple_switch/simple_switch \
    --config ./configs/inc_clients.json \
    --pcap-dump \
    --json simple_router.json
exit
    --disable-cache \
    --client-cmd "../simple_store/client_inc.py -n 1 -c 50 %h %p" \
    --server-cmd "../simple_store/store.py -p %p --log store.log" \
    --num-clients 2 \
    --server-delay 2 \
    --client-delay 1 \
    --config ./configs/test_switch.json \
