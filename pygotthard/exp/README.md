# Microbenchmark Experiments

The topology for these experiments has two machines (node95 and node96)
connected with a switch.

The clients all run on node95, and the store runs on node96. All packets on UDP
port 1234 will be processed with gotthard logic at the switch. All other
packets (i.e. not UDP port 1234) will be forwarded normally.

To use the same setup to test both the baseline and gotthard, we run two store
processes on node96: one listening on port 1234, and one on port 1235. To run
in gotthard mode, packets should be directed at port 1234, whereas for baseline
mode, they should be directed at port 1235.

## Network Configuration

On each machine, we used a network namespace for each port connected to the
switch. To setup the namespace, on node95 we ran:

    theo@node95:~$ ./netns_eth0.sh

and on node96:

    theo@node96:~$ ./netns_eth8.sh

Note that these scripts have hard-coded MAC addresses that should be replaced
with your values.

## Creating an experiment

Edit the `make_experiment.sh` script with the parameters for the experiment you
want to run. Also make sure that the paths to the executables and names of
network namespaces are correct. Then, create the experiment directory:

    theo@node95:~$ ./make_experiment.sh "my_experiment"


## Running an experiment

First, ensure that both of the stores (gotthard and baseline) are running on
the server (node96):

    theo@node96:~$ sudo ip netns exec ns_eth8 ./store.py -j8 -v1 -p 1234 # gotthard port
    theo@node96:~$ sudo ip netns exec ns_eth8 ./store.py -j8 -v1 -p 1235 # baseline port

Start all tests in the experiments directory:

    theo@node95:~$ ./runner.sh "my_experiment"


## Parsing and plotting the results

    theo@node95:~$ time nice -n 18 ./parse_results.py my_experiment/done > my_experiment.tsv
    theo@node95:~$ nice -n 18 ~/s/plot_all_variables.py -l mode -i num_clients,write_ratio,duration,zipf -I write_ratio,num_clients,zipf -d avg_txn_rate,avg_txn_lat,store_msgs_per_txn,store_cpu_pct -c plot.config --out-tsv --skip-single -o plots my_experiment.tsv

To plot a latency CDF, first you have to get all the latencies from the results files:

    ./getlats.py my_experiment/done/8num_clients_0.2write_ratio_180duration/out/{gotthard_results.json,baseline_results.json}

Then you can plot the CDF:

    ~/s/cdf2.py my_experiment/done/8num_clients_0.2write_ratio_180duration/out/baseline_results.json_lats.tsv OCC my_experiment/done/8num_clients_0.2write_ratio_180duration/out/gotthard_results.json_lats.tsv NOCC

