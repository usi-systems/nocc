#!/bin/bash


if [ $# -lt 1 ]; then
    echo "Usage: $0 EXPERIMENTS_DIR"
    exit 1
else
    EXPERIMENTS_DIR=$1
fi

DONE_DIR="$EXPERIMENTS_DIR/done"
TORUN_DIR="$EXPERIMENTS_DIR/torun"

while true
do
    killall python

    experiment_dirname=$(ls -rt $TORUN_DIR | head -n1)
    if [ -z $experiment_dirname ] ; then
        break
    fi

    experiment_dir="$TORUN_DIR/$experiment_dirname"
    echo $experiment_dir

    json_file="$experiment_dir/experiment.json"
    mkdir "$experiment_dir/logs"
    time ./run_experiment.sh $json_file > "$experiment_dir/logs/stdout" 2> "$experiment_dir/logs/stderr"

    mv $experiment_dir $DONE_DIR

done
