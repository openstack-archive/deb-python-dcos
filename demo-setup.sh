#!/bin/bash 

PROJ_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source $PROJ_DIR/teardown.sh

sleep 3

source $PROJ_DIR/setup.sh

echo "pausing 10 mins for the prefetch to complete!"
echo "you can cancel, comeback and run: source ./prompt.sh"

sleep 10m

echo "setting up for DCOS demo"

source $PROJ_DIR/prompt.sh

echo "DCOS demo environment setup complete!"
