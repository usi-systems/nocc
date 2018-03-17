#!/bin/bash

source generic_experiment.sh

duration=300
for num_clients in $(seq 2 16)
do
    exp_name="$num_clients"num_clients_"$duration"duration
    exp_dir=$TORUN_DIR/$exp_name
    mkdir $exp_dir

    echo "#!/bin/bash" > $exp_dir/run.sh
    echo "sleep 5" >> $exp_dir/run.sh
    echo "sudo ip netns exec ns_eth0 /home/theo/src/tpcc/pytpcc/tpcc.py --config=\"\$BASEDIR/gotthard_tpcc.config\" --duration $duration --warehouses 1 --stop-on-error --clients $num_clients --no-load gotthard > out/gotthard_results.txt" >> $exp_dir/run.sh
    echo "sleep 5" >> $exp_dir/run.sh
    echo "sudo ip netns exec ns_eth0 /home/theo/src/tpcc/pytpcc/tpcc.py --config=\"\$BASEDIR/baseline_tpcc.config\" --duration $duration --warehouses 1 --stop-on-error --clients $num_clients --no-load gotthard > out/baseline_results.txt" >> $exp_dir/run.sh
    chmod +x $exp_dir/run.sh
done
