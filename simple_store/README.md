# Simple Store
A key/value store that support r/w operations.

## Running
Start the store server:

    python store.py -p 9090

Run some basic tests:

    python test.py 127.0.0.1 9090

## Increment Clients
Start two clients that increment a counter 1000 times each:

    python client_inc.py -n 2 -c 1000 127.0.0.1 9090

Make sure to restart the server first!

## Software Cache Switch
The cache switch logic is implemented in `software_switch.py`. It acts as a proxy between the clients and the store.

### Example
Start the server:

    python store.py -p 9090

In another terminal, start the software switch listening on port `9091`:

    python software_switch.py -p 9091 127.0.0.1 9090

Run some clients, connecting to the software switch (N.B. they are connecting to the software switch's port, *not* the store's):

    python client_inc.py -n 2 -c 1000 127.0.0.1 9091

You will notice that the store never sends reject messages, because those are handled by the switch.
