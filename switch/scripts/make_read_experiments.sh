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
do
    for TD in 50
    do
        #for N in 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16
        #for N in 15 17 18 19 20 21 22 23
        for N in 15
        do
            #for write_p in 0.5
            for write_p in 0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9 1
            #for write_p in 0.05 0.15 0.25 0.35 0.45 0.55 0.65 0.75 0.85 0.95
            do
                for switch_mode in 'read_cache' 'forward' 'early_abort' 'optimistic_abort'
                do
                        #-c  "../pygotthard/load_generator.py -t %think% -v %think_var% -n %num_clients% -d %runtime% -T A(x,x)W(x,RND)|R(x) -p %write_p% -l %l %h %p" \
                        #-c  "../pygotthard/load_generator.py -n %num_clients% -d %runtime% -T A(x,x)W(x,RND)|R(x) -p %write_p% -l %l %h %p" \
                        #-p think=0.000050 -p think_var=0.1 \
                        #-c  "../pygotthard/load_generator.py -n %num_clients% -c %num_txns% -T A(x,x)W(x,RND)|R(x) -p %write_p% -l %l %h %p" \
                    python gen_experiment.py --stdout-log --sequential-clients \
                        -c  "../pygotthard/load_generator.py -n %num_clients% -t %think% -d %runtime% -T A(x,x)W(x,x+1)|R(x) -p %write_p% -l %l %h %p" \
                        --server-cmd  "../pygotthard/store.py -l %l -p %p" \
                        --out-parent $TORUN_DIR --mode $switch_mode \
                        -p think=0.001 \
                        -p num_clients=$N -p runtime=180 -p write_p=$write_p \
                        --total-delta $TD --delta-ratio $DR
                done
            done
        done
    done
done

