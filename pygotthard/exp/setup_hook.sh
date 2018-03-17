#!/bin/bash

# For TPCC: connect to the switch controller and clear the cached values

ssh node199 tmux send-keys -t gotthard:2.0 C-a C-k c20000 Enter
sleep 2
