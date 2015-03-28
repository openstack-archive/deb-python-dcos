#!/bin/bash 

PROJ_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLUSTER_SIZE=10

echo "Tearing down DCOS demo"

source "$PROJ_DIR/uninstall-apps.sh"
source "$PROJ_DIR/uninstall-services.sh"

echo "Resize cluster to $CLUSTER_SIZE"
dcos resize $CLUSTER_SIZE

echo "Teardown complete!"

./done-dcos.sh
