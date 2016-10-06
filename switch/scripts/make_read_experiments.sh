#!/bin/bash

if [ $# -lt 1 ]; then
    EXPERIMENTS_DIR=experiments
else
    EXPERIMENTS_DIR=$1
fi

for DR in 0.01 0.1 0.5 0.75
do
    for TD in 50
    do
        for N in 2 3 4
        do
            for write_p in 0.05 0.1 0.3 0.5 0.7 0.9
            do
                for switch_mode in 'read_cache' 'forward' 'early_abort' 'optimistic_abort'
                do
                    python gen_experiment.py --stdout-log --sequential-clients \
                        -c  "../pygotthard/load_generator.py -n %num_clients% -c %txn_cnt% -T A(1,a)W(1,RND)|R(1) -p %write_p% -l %l %h %p" \
                        --server-cmd  "../pygotthard/store.py -l %l -p %p" \
                        --out-parent $EXPERIMENTS_DIR --mode $switch_mode \
                        -p num_clients=$N -p txn_cnt=1000 -p write_p=$write_p \
                        --total-delta $TD --delta-ratio $DR
                done
            done
        done
    done
done

