# Gotthard P4 Implementation

## Running
Start the mininet with the switch:

    ./run_demo.sh

And in another terminal, add the table entries:

    ./add_entries.sh

## Read/Write Example
After starting the mininet, use the prompt to start the store on `h2`:

    mininet> h2 python ../simple_store/store.py -p 9999 &

Then, add a key, read it and then read/write it:

    mininet> h1 ../simple_store/write.py h2 9999 1 a
    STATUS_OK
    mininet> h1 ../simple_store/read.py h2 9999 1
    1 a
    mininet> h1 ../simple_store/readwrite.py h2 9999 1 1 1 b
    STATUS_OK
    mininet> h1 ../simple_store/readwrite.py h2 9999 1 1 1 c
    STATUS_REJECT
    mininet> 

## Checking P4 registers
Read the version register for key 1:

    ./read_register.sh version_register 1

Read the value register for key 1:

    ./read_register.sh value_register 1
