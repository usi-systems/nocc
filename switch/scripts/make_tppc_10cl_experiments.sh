#!/bin/bash

if [ $# -lt 1 ]; then
    EXPERIMENTS_DIR=experiments
else
    EXPERIMENTS_DIR=$1
fi

DONE_DIR="$EXPERIMENTS_DIR/done"
TORUN_DIR="$EXPERIMENTS_DIR/torun"
mkdir -p $DONE_DIR
mkdir -p $TORUN_DIR

for DR in 0.2
#for DR in 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9
#for DR in 0.05 0.15 0.25 0.35 0.45 0.55 0.65 0.75 0.85 0.95
#for DR in 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 0.05 0.15 0.25 0.35 0.45 0.55 0.65 0.75 0.85 0.95
do
    #for TD in 50 100
    for TD in 50
    do
        #for N in 8
        for N in 2 3 4 5 6 7 8 9 10 11 12
        do
            for switch_mode in 'read_cache' 'forward' 'early_abort' 'optimistic_abort'
            do
                experiment_file=$(python gen_experiment.py --stdout-log --sequential-clients \
                    -c  "/root/src/tpcc/pytpcc/tpcc.py --config=%e/p4_tpcc_10cl.config --no-load --duration 180 --warehouses 1 --stop-on-error --debug --clients %num_clients% gotthard" \
                    --server-cmd  "../pygotthard/store.py -l %l -p %p -r /tmp/tpcc_10cl.bin" \
                    --out-parent $TORUN_DIR --mode $switch_mode -p num_clients=$N \
                    --total-delta $TD --delta-ratio $DR)
                echo $experiment_file
                experiment_dir=$(dirname $experiment_file)
                logs_dir="$experiment_dir/logs"
                tpcc_config_file="$experiment_dir/p4_tpcc_10cl.config"
                cp ./p4_tpcc_10cl.config $tpcc_config_file
                sed -i -n '/logdir/ !p' $tpcc_config_file
                echo "logdir = $logs_dir" >> $tpcc_config_file
            done
        done
    done
done

