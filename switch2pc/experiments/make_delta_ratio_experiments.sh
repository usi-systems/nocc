#!/bin/bash

if [ $# -lt 1 ]; then
    echo "Usage: $0 EXPERIMENTS_DIR"
    exit 1
else
    EXPERIMENTS_DIR=$1
fi

DONE_DIR="$EXPERIMENTS_DIR/done"
TORUN_DIR="$EXPERIMENTS_DIR/torun"
ERROR_DIR="$EXPERIMENTS_DIR/error"
mkdir -p $DONE_DIR $TORUN_DIR $ERROR_DIR

nthreads=4
duration=90

for nclients in 1 2 4 8
do
    for latency_ms in 0 4 8 16 32 64 128 160
    do
        for router in forward twopc
        do
            json_file=$(./gen_p4app_manifest.py -m p4app_"$router"_template.json -o $TORUN_DIR \
                latency=$latency_ms duration=$duration threads=$nthreads clients=$nclients router=$router)
            echo $json_file

            exp_dir=$(dirname $json_file)

            cat > $exp_dir/run.sh <<EOF
#!/bin/bash
cd "\$(dirname "\$0")"
cp "$(basename $json_file)" "$HOME/src/gotthard/switch2pc/twopc.p4app/experiment_p4app.json"
"$HOME/src/p4app/p4app" run "$HOME/src/gotthard/switch2pc/twopc.p4app" --manifest experiment_p4app.json
rc=\$?
mkdir logs
cp -r /tmp/p4app_logs/*{.log,.stdout} logs
rm "$HOME/src/gotthard/switch2pc/twopc.p4app/experiment_p4app.json"
exit \$rc
EOF

            chmod +x $exp_dir/run.sh
        done
    done
done
