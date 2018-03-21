#!/bin/bash

source generic_experiment.sh

for num_clients in $(seq 2 2 40)
do
    #for write_ratio in 0.0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1.0
    #for write_ratio in 0.05 0.15 0.25 0.35 0.45 0.55 0.65 0.75 0.85 0.95
    for write_ratio in 0.2
    do
        for duration in 300
        do
            exp_name="$num_clients"num_clients_"$write_ratio"write_ratio_"$duration"duration
            exp_dir=$TORUN_DIR/$exp_name
            mkdir $exp_dir

            echo "#!/bin/bash" > $exp_dir/run.sh
            echo "sleep 5" >> $exp_dir/run.sh
            echo "sudo ip netns exec ns_eth0 /home/theo/src/gotthard/pygotthard/load_generator.py -n $num_clients -d $duration -p $write_ratio -T \"A(x,x)W(x,x+1)|R(x)\" -s out/gotthard_results.json 192.168.1.13 1234" >> $exp_dir/run.sh
            echo "sleep 5" >> $exp_dir/run.sh
            echo "sudo ip netns exec ns_eth0 /home/theo/src/gotthard/pygotthard/load_generator.py -n $num_clients -d $duration -p $write_ratio -T \"A(x,x)W(x,x+1)|R(x)\" -s out/baseline_results.json 192.168.1.13 1235" >> $exp_dir/run.sh
            chmod +x $exp_dir/run.sh
        done
    done
done
