#!/bin/bash

NUM_PARTICIPANTS=$1

ADDR_LIST=""

for n in $(seq 1 $NUM_PARTICIPANTS)
do
    port=$((8000+n))
    ADDR_LIST="$ADDR_LIST 127.0.0.1:$port"
    (set -x
    ./participant.py -p $port -t 1 &
    #python -m cProfile -o part.prof ./participant.py -p $port -t 1 &
    )
done

(set -x
./coordinator.py -p 9000 -t 10 $ADDR_LIST
#python -m cProfile -o coo.prof ./coordinator.py -t 1 -p 9000 $ADDR_LIST
)

pkill -P $$

