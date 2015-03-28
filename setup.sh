#!/bin/bash 

CLUSTER_SIZE=20
PROJ_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Setting up for DCOS demo"

source $PROJ_DIR/use-dcos.sh

echo "Setting cluster size to $CLUSTER_SIZE"
dcos resize $CLUSTER_SIZE

echo "Setting up pre-fetch"
dcos marathon start ./demo/pre-fetch.json
dcos marathon scale pre-fetch $CLUSTER_SIZE

echo "Wait a few minutes for the pre-fetch to complete"
echo "checkout: http://demo-bliss.mesosphere.com:3000/overview"
