#!/bin/bash


BMV2_PATH=${P4BENCHMARK_ROOT:?}/behavioral-model
P4C_BM_PATH=$P4BENCHMARK_ROOT/p4c-bm
P4C_BM_SCRIPT=$P4C_BM_PATH/p4c_bm/__main__.py


PROG="gotthard_router"

python loop_tables_template.py -m 2 > loop_tables_generated.p4 

set -m
$P4C_BM_SCRIPT $PROG.p4 --p4-v1.1 --json $PROG.json

if [ $? -ne 0 ]; then
echo "p4 compilation failed"
exit 1
fi

SWITCH_PATH=$BMV2_PATH/targets/simple_switch/simple_switch

CLI_PATH=$BMV2_PATH/tools/runtime_CLI.py

sudo echo "sudo" > /dev/null
sudo $SWITCH_PATH >/dev/null 2>&1
sudo $SWITCH_PATH $PROG.json \
    -i 1@eth18 -i 2@eth20 \
    --log-console &

sleep 2
echo "**************************************"
echo "Sending commands to switch through CLI"
echo "**************************************"
$CLI_PATH --json $PROG.json < physical_interface_commands.txt
echo "READY!!!"
fg
