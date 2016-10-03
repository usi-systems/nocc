#!/bin/bash


if [ $# -lt 1 ]; then
    EXPERIMENTS_DIR=experiments
else
    EXPERIMENTS_DIR=$1
fi

for experiment_name in $(ls $EXPERIMENTS_DIR)
do
    killall python
    echo $experiment_name
    ./run_experiment.sh "$EXPERIMENTS_DIR/$experiment_name/experiment.json" > "$EXPERIMENTS_DIR/$experiment_name/stdout" 2> "$EXPERIMENTS_DIR/$experiment_name/stderr"
done
