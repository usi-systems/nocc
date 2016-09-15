#!/bin/bash

for D in 1 2 3 4 6 8 10
do
    for t in 0 0.0001 0.001 0.01 0.05 0.1 0.2
    do
        for v in 0 0.1 0.3
        do
            for disable_cache in "" "--disable-cache"
            do
                for N in 2 3 4 5
                do
                    python gen_experiment.py \
                        --client-cmd "../simple_store/client_inc.py -c %c -t %t -v %v -l %l %h %p" \
                        --server-cmd "../simple_store/store.py -p %p -l %l" \
                        --out-parent experiments $disable_cache \
                        --req-count 100 --num-clients $N --think-time $t --think-var $v \
                        --client-delta 1 --server-delta $D
                done
            done
        done
    done
done
