COMMON_LOG_SCRIPT_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
source "${COMMON_LOG_SCRIPT_DIR}/term.sh"

function log::info() {
    echo $*
}

function log::err() {
    style::red $* >&2
}

function log::warn() {
    style::yellow $*
}

function log::ok() {
    echo "$(style::green ✔) $*"
}

# vim: set expandtab ts=4 ft=bash iskeyword+=\: :