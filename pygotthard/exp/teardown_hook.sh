#!/bin/bash

# XXX these should be in ENV of the invoking script:
#EXPERIMENTS_NAME=tpcc_inv_thu_mar_15_0151
#EXPERIMENTS_DIR=$EXPERIMENTS_NAME
#RESULTS_DIR=results

TIMEFORMAT="parsed results in %R seconds"

time nice -n 18 ./parse_tpcc_results.py $EXPERIMENTS_DIR/done > $RESULTS_DIR/"$EXPERIMENTS_NAME".tsv && \
    nice -n 18 ~/s/plot_all_variables.py -l mode \
        -i duration,num_clients \
        -I num_clients \
        -d total_rate,payment_rate,order_status_rate,payment_store_aborts_per_txn,order_status_store_aborts_per_txn,store_cpu_pct \
        -c plot.config --out-tsv --skip-single \
        -o plots/"$EXPERIMENTS_NAME" \
        $RESULTS_DIR/$EXPERIMENTS_NAME.tsv
