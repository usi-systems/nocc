#!/bin/bash

PROG="gotthard_router"

THIS_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

source $THIS_DIR/env.sh

P4C_BM_SCRIPT=$P4C_BM_PATH/p4c_bm/__main__.py

SWITCH_PATH=$BMV2_PATH/targets/simple_switch/simple_switch

CLI_PATH=$BMV2_PATH/tools/runtime_CLI.py

echo $P4C_BM_SCRIPT p4src/$PROG.p4 --json $PROG.json --p4-v1.1
$P4C_BM_SCRIPT p4src/$PROG.p4 --json $PROG.json --p4-v1.1
sudo python experiment.py \
    --behavioral-exe $BMV2_PATH/targets/simple_switch/simple_switch \
    --client-cmd "../simple_store/client_inc.py -n 1 -c 70 %h %p" \
    --server-cmd "../simple_store/store.py -p %p" \
    --num-clients 2 \
    --server-delay 2 \
    --client-delay 1 \
    --pcap-dump \
    --json $PROG.json
exit
    --disable-cache \
    --config ./configs/test_switch.json \
    --config ./configs/inc_clients.json \
