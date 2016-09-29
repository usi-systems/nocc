#!/bin/bash

PROG="gotthard_router"

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
shift

last_src_change=$(find p4src -exec stat {} --printf="%Y\n" \; | sort -nr | head -n1)
if [ ! -f $PROG.json ] || [ $(stat -c%Y $PROG.json) -lt $last_src_change ]
then
    echo "Recompiling P4 program"
    python p4src/loop_tables.template.py -m 4 > p4src/loop_tables.generated.p4
    $P4C_BM_SCRIPT p4src/$PROG.p4 --json $PROG.json --p4-v1.1
fi
sudo python experiment.py \
    --behavioral-exe $BMV2_PATH/targets/simple_switch/simple_switch \
    --config $CONF_FILE \
    --pcap-dump \
    --json $PROG.json $@
