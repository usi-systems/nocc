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

TD=50
num_keys=10
for DR in 0.2
#for DR in 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9
#for DR in 0.05 0.15 0.25 0.35 0.45 0.55 0.65 0.75 0.85 0.95
do
    #for zipf_s in 1 2 3 4 5 6
    for zipf_s in 0 0.5
    #for zipf_s in 1.5 2.5 3.5 4.5 5.5
    do
        #for N in 11 12 13 14 15 16
        #for N in 2 3 4 5 6 7 9 10 11 12 13 14
        for N in 8
        do
            for write_p in 0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1
            #for write_p in 0.05 0.15 0.25 0.35 0.45 0.55 0.65 0.75 0.85 0.95
            do
                for switch_mode in 'read_cache' 'forward' 'optimistic_abort'
                do
                    zipf_params=$(./scripts/zipf.py -n $num_keys -w $write_p -s $zipf_s)
                    probabilities=$(echo $zipf_params | awk '{print $1}')
                    txns=$(echo $zipf_params | awk '{print $2}')
                    python gen_experiment.py --stdout-log --sequential-clients \
                        -c  "../pygotthard/load_generator.py -n %num_clients% -d %runtime% -p $probabilities -T $txns -l %l %h %p" \
                        --server-cmd  "../pygotthard/store.py -l %l -p %p" \
                        --out-parent $TORUN_DIR --mode $switch_mode \
                        -p num_clients=$N -p runtime=60 -p write_p=$write_p \
                        -p zipf_s=$zipf_s -p num_keys=$num_keys \
                        --total-delta $TD --delta-ratio $DR
                done
            done
        done
    done
done

