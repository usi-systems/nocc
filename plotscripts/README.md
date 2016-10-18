# Graph Plotting Scripts

## Examples

    ./plot_all_variables.py --out-tsv --skip-single -c plot.config --label mode \
            -d all_txn_rate,all_txn_latency,switch_abort_ratio,duration \
            -i delta_ratio,num_clients,write_p,total_delta \
            -I write_p,num_clients,delta_ratio \
            --out-dir plots results.tsv


    ./plot_lines.py -f pdf -c plot.config label_x_y_err.tsv


### Bar Chart
First, generate the data:

    cat results.tsv | q -t -H -O "SELECT mode, tpcc_total_rate, tpcc_payment_rate, tpcc_delivery_rate, tpcc_new_order_rate, tpcc_stock_level_rate, tpcc_order_status_rate FROM - WHERE delta_ratio=0.2 AND num_clients=8" > barchart.tsv

Then plot it:

    ./plot_lines.py --no-error --bar -c plot.config barchart.tsv
