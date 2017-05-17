#!/usr/bin/env bash

# This script expects the following env vars:
#   CCM_AUTH_TOKEN
#   CLUSTER_ID

set -o errexit -o nounset -o pipefail

http --ignore-stdin --check-status --follow DELETE https://ccm.mesosphere.com/api/cluster/${CLUSTER_ID}/ Authorization:"Token ${CCM_AUTH_TOKEN}"
