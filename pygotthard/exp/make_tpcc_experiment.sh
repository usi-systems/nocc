#!/bin/bash

BASEDIR=$(dirname "$0")

if [ $# -lt 1 ]; then
    echo "Usage: $0 EXPERIMENTS_DIR"
    exit 1
else
    EXPERIMENTS_DIR=$1
fi

DONE_DIR="$EXPERIMENTS_DIR/done"
TORUN_DIR="$EXPERIMENTS_DIR/torun"
mkdir -p $DONE_DIR
mkdir -p $TORUN_DIR

duration=300
for num_clients in 2 4 8 16 24 32 40
do
    exp_name="$num_clients"num_clients_"$duration"duration
    exp_dir=$TORUN_DIR/$exp_name
    mkdir $exp_dir

    echo "#!/bin/bash" > $exp_dir/run.sh
    echo "sudo ip netns exec ns_eth0 /home/theo/src/tpcc/pytpcc/tpcc.py --config=\"\$BASEDIR/gotthard_tpcc.config\" --duration $duration --warehouses 1 --stop-on-error --clients $num_clients --no-load gotthard > out/gotthard_results.txt" >> $exp_dir/run.sh
    echo "sleep 5" >> $exp_dir/run.sh
    echo "sudo ip netns exec ns_eth0 /home/theo/src/tpcc/pytpcc/tpcc.py --config=\"\$BASEDIR/baseline_tpcc.config\" --duration $duration --warehouses 1 --stop-on-error --clients $num_clients --no-load gotthard > out/baseline_results.txt" >> $exp_dir/run.sh
    chmod +x $exp_dir/run.sh
done
