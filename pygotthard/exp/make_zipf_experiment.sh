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

duration=180
num_keys=10
for num_clients in 8
do
    for write_ratio in 0.2
    do
        for zipf_s in 0 1 2 3 4 5 6
        do
            exp_name="$num_clients"num_clients_"$write_ratio"write_ratio_"$zipf_s"zipf_"$duration"duration
            exp_dir=$TORUN_DIR/$exp_name
            mkdir $exp_dir

            echo "#!/bin/bash" > $exp_dir/run.sh
            echo "sudo ip netns exec ns_eth0 /home/theo/src/gotthard/pygotthard/load_generator.py -n $num_clients -d $duration --zipf $zipf_s --keys $num_keys --write-ratio $write_ratio -s out/gotthard_results.json 192.168.1.13 1234" >> $exp_dir/run.sh
            echo "sleep 5" >> $exp_dir/run.sh
            echo "sudo ip netns exec ns_eth0 /home/theo/src/gotthard/pygotthard/load_generator.py -n $num_clients -d $duration --zipf $zipf_s --keys $num_keys --write-ratio $write_ratio -s out/baseline_results.json 192.168.1.13 1235" >> $exp_dir/run.sh
            chmod +x $exp_dir/run.sh
        done
    done
done
