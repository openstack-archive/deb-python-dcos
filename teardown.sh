#!/bin/bash 

PROJ_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLUSTER_SIZE=10

echo "tearing down dcos demo"

source "$PROJ_DIR/uninstall-apps.sh"
source "$PROJ_DIR/uninstall-services.sh"

dcos resize $CLUSTER_SIZE

echo "teardown complete!"
