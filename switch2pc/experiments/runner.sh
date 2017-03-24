#!/bin/bash

if [ $# -lt 1 ]; then
    echo "Usage: $0 EXPERIMENTS_DIR"
    exit 1
else
    EXPERIMENTS_DIR=$1
fi

DONE_DIR="$EXPERIMENTS_DIR/done"
TORUN_DIR="$EXPERIMENTS_DIR/torun"
RUNNING_DIR="$EXPERIMENTS_DIR/running"
ERROR_DIR="$EXPERIMENTS_DIR/error"
mkdir -p $RUNNING_DIR $ERROR_DIR

while true
do

    experiment_dirname=$(ls -rt $TORUN_DIR | head -n1)
    if [ -z $experiment_dirname ] ; then
        break
    fi

    mv "$TORUN_DIR/$experiment_dirname" "$RUNNING_DIR/"
    experiment_dir="$RUNNING_DIR/$experiment_dirname"
    echo $experiment_dir
    rm -rf $experiment_dir/out
    mkdir $experiment_dir/out

    (cd $experiment_dir && time ./run.sh > out/stdout 2> out/stderr)
    rc=$?

    sleep 8
    [ $rc -eq 0 ] && mv $experiment_dir $DONE_DIR || mv $experiment_dir $ERROR_DIR

done

