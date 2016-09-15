#!/bin/bash

THIS_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

source $THIS_DIR/env.sh

P4C_BM_SCRIPT=$P4C_BM_PATH/p4c_bm/__main__.py

SWITCH_PATH=$BMV2_PATH/targets/simple_switch/simple_switch

CLI_PATH=$BMV2_PATH/tools/runtime_CLI.py

if [ $# -lt 1 ]; then
    echo "Please specify experiment JSON conf file"
    exit 1
fi
CONF_FILE=$1

$P4C_BM_SCRIPT p4src/$PROG.p4 --json $PROG.json --p4-v1.1
sudo python experiment.py \
    --behavioral-exe $BMV2_PATH/targets/simple_switch/simple_switch \
    --config $CONF_FILE \
    --pcap-dump \
    --json $PROG.json
