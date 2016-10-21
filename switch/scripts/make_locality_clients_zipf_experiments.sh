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
num_keys=5
DR=0.2
#for locality in 0.5 1.0 0.75
for locality in 0.625 0.875 0.5 1.0 0.75
do
    #for zipf_s in 1 2 3 4 5 6
    #for zipf_s in 0.5 1.5 2.5 3.5 4.5 5.5
    for zipf_s in 3
    do
        for N in 16
        do
            for write_p in 0.2
            do
                for switch_mode in 'read_cache' 'forward' 'optimistic_abort'
                do
                    clients_per_side=$(echo "$N / 2" | bc)
                    lcl_cnt=$(echo "($clients_per_side * $locality) / 1" | bc)
                    rem_cnt=$(echo "$clients_per_side - $lcl_cnt" | bc)

                    s2_zipf_params=$(./scripts/zipf.py -n $num_keys -w $write_p -s $zipf_s -k a,b,c,d,e,f,g,h,i,j)
                    s2_probabilities=$(echo $s2_zipf_params | awk '{print $1}')
                    s2_txns=$(echo $s2_zipf_params | awk '{print $2}')

                    s3_zipf_params=$(./scripts/zipf.py -n $num_keys -w $write_p -s $zipf_s -k q,r,s,t,u,v,w,x,y,z)
                    s3_probabilities=$(echo $s3_zipf_params | awk '{print $1}')
                    s3_txns=$(echo $s3_zipf_params | awk '{print $2}')

                    python gen_experiment.py --stdout-log \
                        -c  "../pygotthard/load_generator.py -i 1000 -n $lcl_cnt -t %think% -d %runtime% -T $s2_txns -p $s2_probabilities -l %l %h %p" \
                            "../pygotthard/load_generator.py -i 1100 -n $rem_cnt -t %think% -d %runtime% -T $s3_txns -p $s3_probabilities -l %l %h %p" \
                            "../pygotthard/load_generator.py -i 2000 -n $lcl_cnt -t %think% -d %runtime% -T $s3_txns -p $s3_probabilities -l %l %h %p" \
                            "../pygotthard/load_generator.py -i 2200 -n $rem_cnt -t %think% -d %runtime% -T $s2_txns -p $s2_probabilities -l %l %h %p" \
                        --switches s2,s2,s3,s3 \
                        --server-cmd  "../pygotthard/store.py -l %l -p %p" \
                        --out-parent $TORUN_DIR --mode $switch_mode \
                        -p think=0.001 -p locality=$locality -p zipf_s=$zipf_s\
                        -p num_clients=$N -p runtime=180 -p write_p=$write_p \
                        --total-delta $TD --delta-ratio $DR
                done
            done
        done
    done
done

