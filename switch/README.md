# Gotthard P4 Implementation

## Tesing

Generate some experiments to test normal forwarding, early abort and optimistic abort modes of the switch:


    gen_experiment.py --num-clients 1 --sequential-clients \
        -c "../pygotthard/test/test_basic.py -l %l %h %p" \
        --server-cmd "../pygotthard/store.py -l %l -p %p" \
        --client-delta 1 --server-delta 2 --mode forward --out-dir test_basic
    gen_experiment.py --num-clients 1 --sequential-clients \
        -c "../pygotthard/test/test_early_abort.py -l %l %h %p" \
        --server-cmd "../pygotthard/store.py -l %l -p %p" \
        --client-delta 1 --server-delta 2 --mode early_abort --out-dir test_early
    gen_experiment.py --num-clients 1 --sequential-clients \
        -c "../pygotthard/test/test_opti_abort.py -l %l %h %p" \
        --server-cmd "../pygotthard/store.py -l %l -p %p" \
        --client-delta 1 --server-delta 50 --mode optimistic_abort --out-dir test_opti

Then, run the experiments:

    ./run_experiment.sh test_basic/experiment.json
    ./run_experiment.sh test_early/experiment.json
    ./run_experiment.sh test_opti/experiment.json
