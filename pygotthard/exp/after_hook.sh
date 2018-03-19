#!/bin/bash

ssh -oIdentitiesOnly=yes -i ~/.ssh/id_rsa cc ~/scripts/notify.sh -s "$EXPERIMENTS_NAME" finished
