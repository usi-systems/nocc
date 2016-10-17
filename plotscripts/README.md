# Graph Plotting Scripts

## Examples

    ./plot_all_variables.py --out-tsv --skip-single -c plot.config --label mode \
            -d all_txn_rate,all_txn_latency,switch_abort_ratio,duration \
            -i delta_ratio,num_clients,write_p,total_delta \
            -I write_p,num_clients,delta_ratio \
            --out-dir plots results.tsv


    ./plot_lines.py -f pdf -c plot.config label_x_y_err.tsv
