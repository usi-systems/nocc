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

DR=0.2
for locality in 0.625 0.875
#for locality in 0.5 0.75 1.0
do
    for TD in 50
    do
        for N in 8
        do
            for write_p in 0.5
            do
                for switch_mode in 'read_cache' 'forward' 'optimistic_abort'
                do
                    clients_per_side=$(echo "$N / 2" | bc)
                    lcl_cnt=$(echo "($clients_per_side * $locality) / 1" | bc)
                    rem_cnt=$(echo "$clients_per_side - $lcl_cnt" | bc)

                    python gen_experiment.py --stdout-log \
                        -c  "../pygotthard/load_generator.py -i 1000 -n $lcl_cnt -t %think% -d %runtime% -T A(x,x)W(x,x+1)|R(x) -p %write_p% -l %l %h %p" \
                          "../pygotthard/load_generator.py -i 1100 -n $rem_cnt -t %think% -d %runtime% -T A(y,y)W(y,y+1)|R(y) -p %write_p% -l %l %h %p" \
                          "../pygotthard/load_generator.py -i 2000 -n $lcl_cnt -t %think% -d %runtime% -T A(y,y)W(y,y+1)|R(y) -p %write_p% -l %l %h %p" \
                          "../pygotthard/load_generator.py -i 2200 -n $rem_cnt -t %think% -d %runtime% -T A(x,x)W(x,x+1)|R(x) -p %write_p% -l %l %h %p" \
                        --switches s2,s2,s3,s3 \
                        --server-cmd  "../pygotthard/store.py -l %l -p %p" \
                        --out-parent $TORUN_DIR --mode $switch_mode \
                        -p think=0.001 -p locality=$locality \
                        -p num_clients=$N -p runtime=60 -p write_p=$write_p \
                        --total-delta $TD --delta-ratio $DR
                done
            done
        done
    done
done

