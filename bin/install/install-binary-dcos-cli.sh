#!/usr/bin/env bash

# Installs and configures the binary DC/OS CLI.
#
# Auto-detects the DC/OS version by asking an existing DC/OS cluster.
# Auto-detects the local operating system to download the right DC/OS CLI binary.
#
# Arguments:
#   dcos-url -- (required) URL to DC/OS cluster (default: http://m1.dcos/)
#   install-dir-path -- (optional) Directory path to install into (default: platform dependent)
#
# Usage:
# $ bin/install/dcos-binary-install-cli.sh <dcos-url> [install-dir-path]
# $ dcos --version
#
# Alt Usage:
# $ EXE="$(ci/dcos-binary-install-cli.sh <dcos-url> [install-dir-path] 2>/dev/null)"
# $ ${EXE} --version
#
# Remote Usage:
# $ curl https://downloads.dcos.io/dcos-cli/bin/install/dcos-binary-install-cli.sh | bash -s <dcos-url> [install-dir-path]
# $ dcos --version

set -o errexit -o nounset -o pipefail

# Show usage information.
function usage() {
  echo "$(basename "$(test -L "$0" && readlink "$0" || echo "$0")") <dcos-url> [install-dir-path]"
}

# Query the DC/OS API for the DC/OS version
function detect_dcos_version() {
  # Auto-detect version (unauthenticated)
  DCOS_VERSION_JSON="$(curl --fail --location --silent --show-error ${DCOS_URL%/}/dcos-metadata/dcos-version.json)"
  # Extract version from metadata
  # Warning: requires json to be pretty-printed with line breaks
  # Full json parsing would require a dependency like python or jq.
  DCOS_VERSION="$(echo "${DCOS_VERSION_JSON}" | grep 'version' | cut -d ':' -f 2 | cut -d '"' -f 2)"
  echo "${DCOS_VERSION}"
}

function create_temp_dir() {
  TMPDIR="${TMPDIR:-/tmp/}"
  CLI_DIR="$(mktemp -d "${TMPDIR%/}/dcos-install-cli.XXXXXXXXXXXX")"
  echo "${CLI_DIR}"
}

function download_cli() {
  CLI_DIR="${1}"
  DCOS_CLI_URL="https://downloads.dcos.io/binaries/cli/${PLATFORM}/dcos-${DCOS_MAJOR_VERSION}/${EXE}"
  echo >&2 "Download URL: ${DCOS_CLI_URL}"
  echo >&2 "Download Path: ${CLI_DIR}/${EXE}"
  curl --fail --location --silent --show-error -o "${CLI_DIR}/${EXE}" "${DCOS_CLI_URL}"
  echo "${CLI_DIR}/${EXE}"
}

function install_cli() {
  DOWNLOAD_PATH="${1}"
  INSTALL_DIR_PATH="${2}"
  INSTALL_PATH="${INSTALL_DIR_PATH}/$(basename "${DOWNLOAD_PATH}")"
  chmod a+x "${DOWNLOAD_PATH}"
  # only use sudo if required
  if [[ -w "${INSTALL_DIR_PATH}" ]]; then
    mv "${DOWNLOAD_PATH}" "${INSTALL_PATH}"
  else
    sudo mv "${DOWNLOAD_PATH}" "${INSTALL_PATH}"
  fi
  echo "${INSTALL_PATH}"
}

if [ "$#" -lt 1 ]; then
  usage;
  exit 1;
fi

DCOS_URL="${1}" #required
echo >&2 "DC/OS URL: ${DCOS_URL}"
INSTALL_DIR_PATH="${2:-}" #optional

DCOS_VERSION="$(detect_dcos_version)"
echo >&2 "DC/OS Version: ${DCOS_VERSION}"

# Get major version by stripping the last version segment
VERSION_PATTERN='[^0-9]*\([0-9]*\)[.]\([0-9]*\).*'
MAJOR_VERSION="$(echo "${DCOS_VERSION}" | sed -e "s#${VERSION_PATTERN}#\1#")"
MINOR_VERSION="$(echo "${DCOS_VERSION}" | sed -e "s#${VERSION_PATTERN}#\2#")"
DCOS_MAJOR_VERSION="${MAJOR_VERSION}.${MINOR_VERSION}"
echo >&2 "DC/OS Major Version: ${DCOS_MAJOR_VERSION}"

case "${OSTYPE}" in
  darwin*)  PLATFORM='darwin/x86-64'; BIN='/usr/local/bin'; EXE='dcos' ;;
  linux*)   PLATFORM='linux/x86-64'; BIN='/usr/local/bin'; EXE='dcos' ;;
  msys*)    PLATFORM='windows/x86-64'; BIN="${HOME}/AppData/Local/Microsoft/WindowsApps"; EXE='dcos.exe' ;;
  *)        echo >&2 "Unsupported operating system: ${OSTYPE}"; exit 1 ;;
esac
INSTALL_DIR_PATH="${INSTALL_DIR_PATH:-${BIN}}"

# Use temp dir to download into before install, delete on script exit
CLI_DIR="$(create_temp_dir)"
trap "rm -rf ${CLI_DIR}" EXIT

DOWNLOAD_PATH="$(download_cli "${CLI_DIR}")"
INSTALL_PATH="$(install_cli "${DOWNLOAD_PATH}" "${INSTALL_DIR_PATH}")"

echo >&2 "Config: core.dcos_url=${DCOS_URL}"
dcos config set core.dcos_url "${DCOS_URL}"

# Log CLI & Cluster versions
echo >&2 "dcos --version"
dcos --version >&2

# Print install path to STDOUT to enable script chaining
echo >&2 "Install Path:"
echo "${INSTALL_PATH}"
