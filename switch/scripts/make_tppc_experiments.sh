#!/bin/bash

if [ $# -lt 1 ]; then
    EXPERIMENTS_DIR=experiments
else
    EXPERIMENTS_DIR=$1
fi

for DR in 0.01 0.1 0.2 0.3 0.4 0.5 0.6 0.75 0.9
do
    for TD in 50 100
    #for TD in 50
    do
        for N in 2 3 4 5 6 8
        do
            for switch_mode in 'read_cache' 'forward' 'early_abort' 'optimistic_abort'
            do
                experiment_file=$(python gen_experiment.py --stdout-log --sequential-clients \
                    -c  "/root/src/tpcc/pytpcc/tpcc.py --config=%e/p4_tpcc.config --no-load --duration 180 --warehouses 1 --stop-on-error --debug --clients %num_clients% gotthard" \
                    --server-cmd  "../pygotthard/store.py -l %l -p %p -r /tmp/tpcc.bin" \
                    --out-parent $EXPERIMENTS_DIR --mode $switch_mode -p num_clients=$N \
                    --total-delta $TD --delta-ratio $DR)
                echo $experiment_file
                experiment_dir=$(dirname $experiment_file)
                logs_dir="$experiment_dir/logs"
                tpcc_config_file="$experiment_dir/p4_tpcc.config"
                cp ./p4_tpcc.config $tpcc_config_file
                sed -i -n '/logdir/ !p' $tpcc_config_file
                echo "logdir = $logs_dir" >> $tpcc_config_file
            done
        done
    done
done

