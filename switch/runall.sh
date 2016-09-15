#!/bin/bash

for experiment_name in $(ls experiments)
do
    killall python
    ./run_experiment.sh "experiments/$experiment_name/experiment.json" > "experiments/$experiment_name/stdout" 2> "experiments/$experiment_name/stderr"
done
