#!/usr/bin/env bash

# This script expects the following env vars:
#   CCM_AUTH_TOKEN
#   CLUSTER_NAME
#   CCM_CLUSTER_REGION (optional)
#   DCOS_CHANNEL (optional)
#   CF_TEMPLATE_NAME (optional)
#   CF_TEMPLATE_URL (optional)

set -o errexit -o nounset -o pipefail

# create cluster
RESPONSE_JSON="$(http --ignore-stdin --follow \
     https://ccm.mesosphere.com/api/cluster/ \
     Authorization:"Token ${CCM_AUTH_TOKEN}" \
     name="${CLUSTER_NAME}" \
     cluster_desc="DC/OS CLI testing cluster" \
     cloud_provider=0 \
     region="${CCM_CLUSTER_REGION:-"eu-central-1"}" \
     time=120 \
     $([[ -n "${DCOS_CHANNEL:-}" ]] && echo "channel=${DCOS_CHANNEL}") \
     $([[ -n "${CF_TEMPLATE_NAME:-}" ]] && echo "template=${CF_TEMPLATE_NAME}") \
     $([[ -n "${CF_TEMPLATE_URL:-}" ]] && echo "template_url=${CF_TEMPLATE_URL}") \
     adminlocation=0.0.0.0/0 \
     public_agents=1 \
     private_agents=1)"

if ! echo "${RESPONSE_JSON}" | jq -e 'has("id")'; then
  echo >&2 "Error: CCM response does not include an id."
  echo >&2 "Response: ${RESPONSE_JSON}"
  exit 1
fi

CLUSTER_ID="$(echo "${RESPONSE_JSON}" | jq -r ".id")"
echo "${CLUSTER_ID}"
