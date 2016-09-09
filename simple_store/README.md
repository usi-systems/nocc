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
