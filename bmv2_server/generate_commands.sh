#/bin/bash

for mode in forward early_abort read_cache optimistic_abort; do cp commands.txt ${mode}_commands.txt; python rules.py --mode $mode >> ${mode}_commands.txt; done
