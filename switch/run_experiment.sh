#!/bin/bash

THIS_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
source $THIS_DIR/env.sh

if [ $# -lt 1 ]; then
    echo "Please specify experiment JSON conf file"
    exit 1
fi
CONF_FILE=$1
shift

SWITCH_MODE=$(cat $CONF_FILE | python -c 'import sys, json; print json.load(sys.stdin)["switch"]["mode"]')

if [ "$SWITCH_MODE" = "optimistic_abort" ]
then
    PROG="gotthard_router"
elif [ "$SWITCH_MODE" = "read_cache" ]
then
    PROG="read_cache_router"
elif [ "$SWITCH_MODE" = "forward" ]
then
    PROG="forward_router"
fi

last_src_change=$(find p4src -exec stat {} --printf="%Y\n" \; | sort -nr | head -n1)
if [ ! -f $PROG.json ] || [ $(stat -c%Y $PROG.json) -lt $last_src_change ]
then
    echo "Recompiling P4 program"
    echo $P4C_PATH/build/p4c-bm2-ss p4src/$PROG.p4 -o $PROG.json --p4-16
    $P4C_PATH/build/p4c-bm2-ss p4src/$PROG.p4 -o $PROG.json --p4-16
fi

sudo python experiment.py \
    --behavioral-exe $BMV2_PATH/targets/simple_switch/simple_switch \
    --config $CONF_FILE \
    --json $PROG.json $@

#    --pcap-dump \
#    --cli \
