# p4image
A Docker image ready to run the p4 v1.1 tutorial.

## Building
Build the container image with:

    docker build -t p4image .

## Running
Make sure to start the container with `--privileged`:

    docker run --privileged -d --name p4 p4image

Then try the tutorial:

    docker exec -it p4 bash
    cd /root/tutorials/p4v1_1/simple_router/
    ./run_demo.sh

