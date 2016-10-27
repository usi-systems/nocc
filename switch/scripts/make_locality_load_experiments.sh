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
#for locality in 0.625 0.875
#for locality in 0.5 0.75 1.0
#for locality in 0.65 0.7 0.8 0.85 0.9 0.95
for locality in 0.5 0.55 0.6 0.65 0.7 0.75 0.8 0.85 0.9 0.95 1
do
    for TD in 50
    do
        for N in 32
        do
            for write_p in 0.2
            do
                for switch_mode in 'read_cache' 'forward' 'optimistic_abort'
                #for switch_mode in 'read_cache' 'optimistic_abort'
                do
                    num_switches=2
                    num_keys=8
                    clients_per_switch=$(echo "$N / $num_switches" | bc)

                    #s2_params=$(./scripts/locality.py -n $num_keys -w $write_p -l $locality -L a,b -k a,b,c,d,e,f,g,h)
                    s2_params=$(./scripts/locality.py -n $num_keys -w $write_p -l $locality -L a,b,c,d -k a,b,c,d,e,f,g,h)
                    #s2_params=$(./scripts/locality.py -n $num_keys -w $write_p -l $locality -L a,b -k a,b,c,d)
                    s2_pdf=$(echo $s2_params | awk '{print $1}')
                    s2_txn=$(echo $s2_params | awk '{print $2}')

                    #s3_params=$(./scripts/locality.py -n $num_keys -w $write_p -l $locality -L c,d -k a,b,c,d,e,f,g,h)
                    s3_params=$(./scripts/locality.py -n $num_keys -w $write_p -l $locality -L e,f,g,h -k a,b,c,d,e,f,g,h)
                    #s3_params=$(./scripts/locality.py -n $num_keys -w $write_p -l $locality -L c,d -k a,b,c,d)
                    s3_pdf=$(echo $s3_params | awk '{print $1}')
                    s3_txn=$(echo $s3_params | awk '{print $2}')

                    s4_params=$(./scripts/locality.py -n $num_keys -w $write_p -l $locality -L e,f -k a,b,c,d,e,f,g,h)
                    s4_pdf=$(echo $s4_params | awk '{print $1}')
                    s4_txn=$(echo $s4_params | awk '{print $2}')

                    s5_params=$(./scripts/locality.py -n $num_keys -w $write_p -l $locality -L g,h -k a,b,c,d,e,f,g,h)
                    s5_pdf=$(echo $s5_params | awk '{print $1}')
                    s5_txn=$(echo $s5_params | awk '{print $2}')

                        #    "../pygotthard/load_generator.py -i 4000 -n $clients_per_switch -t %think% -d %runtime% -T $s4_txn -p $s4_pdf -l %l %h %p" \
                        #    "../pygotthard/load_generator.py -i 5000 -n $clients_per_switch -t %think% -d %runtime% -T $s5_txn -p $s5_pdf -l %l %h %p" \
                        #--switch s4 --switch s5 \
                    python gen_experiment.py --stdout-log \
                        -c  "../pygotthard/load_generator.py -i 2000 -n $clients_per_switch -t %think% -d %runtime% -T $s2_txn -p $s2_pdf -l %l %h %p" \
                            "../pygotthard/load_generator.py -i 3000 -n $clients_per_switch -t %think% -d %runtime% -T $s3_txn -p $s3_pdf -l %l %h %p" \
                        --switch s2 --switch s3 \
                        --server-cmd  "../pygotthard/store.py -l %l -p %p" \
                        --out-parent $TORUN_DIR --mode $switch_mode \
                        -p locality=$locality -p write_p=$write_p \
                        -p num_keys=$num_keys \
                        -p num_clients=$N -p num_switches=$num_switches \
                        -p think=0.001 -p runtime=180 \
                        --total-delta $TD --delta-ratio $DR
                done
            done
        done
    done
done

