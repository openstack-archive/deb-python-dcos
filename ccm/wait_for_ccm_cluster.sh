#!/usr/bin/env bash

# This script expects the following env vars:
#   CCM_AUTH_TOKEN
#   CLUSTER_ID

set -o errexit -o nounset -o pipefail

# wait for cluster to come up
while true; do
    STATUS=$(http --ignore-stdin \
                  https://ccm.mesosphere.com/api/cluster/${CLUSTER_ID}/ \
                  Authorization:"Token ${CCM_AUTH_TOKEN}" | \
                    jq ".status");
    if [ "${STATUS}" -eq 0 ]; then
        CLUSTER_INFO=$(http GET https://ccm.mesosphere.com/api/cluster/${CLUSTER_ID}/ Authorization:"Token ${CCM_AUTH_TOKEN}" | jq ".cluster_info")

         # ensure cluster_info is populated
         if [ ! -z "$CLUSTER_INFO" ]; then
            eval CLUSTER_INFO=$CLUSTER_INFO  # unescape json
            break;
         fi;
    fi;
    sleep 10;
done;

echo "$(echo "${CLUSTER_INFO}" | jq -r ".MastersIpAddresses[0]")"
