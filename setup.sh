#!/bin/bash 

CLUSTER_SIZE=10

echo "setting up for dcos demo"

echo "setting cluster size to $CLUSTER_SIZE"
dcos resize $CLUSTER_SIZE

echo "setting up pre-fetch"
dcos marathon start ./demo/pre-fetch.json
dcos marathon scale pre-fetch $CLUSTER_SIZE

echo "wait a few minutes for the pre-fetch to complete"
echo "checkout: http://demo-bliss.mesosphere.com:3000/overview"
