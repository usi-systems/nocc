# Simple Store
A key/value store that support r/w operations.

## Running
Start the store listenning on port 9999:

    ./store.py -p 9999

Start the switch:

    ./software_switch.py -p 9991 -d 0.001 -D 0.01 -v 1 -m optimistic_abort 127.0.0.1 9999

Where:
  - `-p 9991`: listen on port 9991
  - `-d 0.001`: simulate client-switch latency of 1ms
  - `-D 0.01`: simulate store-switch latency of 10ms
  - `-v 1`: verbosity level 1
  - `-m optimistic_abort`: use optimistic abort mode

## Tests
Once the store and switch are running, test that optimistic abort works:

    ./test/test_opti_abort.py 127.0.0.1 9991

To test the other modes, you have to stop the switch, and restart it with another mode. For example, to test `early_abort` mode, start the switch with the option `-m early_abort`, and run the test:

    ./test/test_early_abort.py 127.0.0.1 9991

## Running a workload

This will run the classic atomic increment with two clients:

    ./load_generator.py -l out.log -n 2 -c 100 -T "A(x,x)W(x,x+1)|R(x)" -p 0.1 127.0.0.1 9999

Where:
  - `-l out.log`: output log
  - `-n 2`: run two clients in parallel
  - `-d 30`: run for 30s
  - `-T "A(x,x)W(x,x+1)|R(x)"`: the TXNs to execute, either `A(x, x)W(x, x+1)` (assert `x`, then increment `x`) or `R(x)` (read `x`).
  - `-p 0.1`: the probability of executing each TXN. If you don't specify all the probabilities, the missing ones will be automatically computed. In this case, the first TXN will be executed with P=0.1 and the second with P=0.9 (automatically computed).

Alternatively, you can run it with `-c 100` to execute 100 TXNs, and then stop.
