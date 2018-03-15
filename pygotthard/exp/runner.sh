#!/bin/bash

BASEDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export BASEDIR

if [ $# -lt 1 ]; then
    echo "Usage: $0 EXPERIMENTS_DIR"
    exit 1
else
    EXPERIMENTS_DIR=$1
fi
export EXPERIMENTS_DIR

if [ ! -d $EXPERIMENTS_DIR ]; then
    echo "Directory does not exist: $EXPERIMENTS_DIR"
    exit 1
fi

EXPERIMENTS_NAME=$(basename $EXPERIMENTS_DIR)
export EXPERIMENTS_NAME

RESULTS_DIR=results
export RESULTS_DIR

DONE_DIR="$EXPERIMENTS_DIR/done"
TORUN_DIR="$EXPERIMENTS_DIR/torun"
RUNNING_DIR="$EXPERIMENTS_DIR/running"
mkdir -p $RUNNING_DIR

run_hook() {
    hook_file=$EXPERIMENTS_DIR/"$1"_hook.sh
    if [ -x $hook_file ]; then
        $hook_file
    fi
}

while true
do

    if [ -f $EXPERIMENTS_DIR/pause ]; then
        echo "Detected pause file. Now exiting. Remove pause file to continue."
        break
    fi

    run_hook before

    experiment_dirname=$(ls -rt $TORUN_DIR | head -n1)
    if [ -z $experiment_dirname ]; then
        break
    fi

    mv "$TORUN_DIR/$experiment_dirname" "$RUNNING_DIR/"
    experiment_dir="$RUNNING_DIR/$experiment_dirname"
    echo $experiment_dir
    mkdir $experiment_dir/out

    (cd $experiment_dir && time ./run.sh > out/stdout 2> out/stderr) 2>&1 | grep real
    echo

    run_hook after

    sleep 1

    mv $experiment_dir $DONE_DIR

done

