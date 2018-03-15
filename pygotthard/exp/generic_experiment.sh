#!/bin/bash

BASEDIR=$(dirname "$0")

if [ $# -lt 1 ]; then
    echo "Usage: $0 EXPERIMENTS_DIR"
    exit 1
else
    EXPERIMENTS_DIR=$1
fi

DONE_DIR="$EXPERIMENTS_DIR/done"
TORUN_DIR="$EXPERIMENTS_DIR/torun"
mkdir -p $DONE_DIR
mkdir -p $TORUN_DIR

for h in before after
do
    if [ -f "$BASEDIR/$h"_hook.sh ] && [ ! -f "$EXPERIMENTS_DIR/$h"_hook.sh ]; then
        cp "$BASEDIR/$h"_hook.sh "$EXPERIMENTS_DIR"
    fi
done
