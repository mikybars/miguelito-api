COMMON_SYS_SCRIPT_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
source "${COMMON_SYS_SCRIPT_DIR}/log.sh"

function sys::exit() {
    log::info $* && exit
}

function sys::warn_and_exit() {
    log::warn $* && exit
}

function sys::fail() {
    log::err $* && exit 1
}

function sys::require_command() {
    local command=$1
    local err_msg="Command '$command' is required."

    if (( $# > 1 )); then
        local install="$2"
        err_msg="$err_msg See '$install'"
    fi

    cmd_exists $command || sys::fail $err_msg
}

function cmd_exists() {
    [[ -x $(command -v $1) ]]
}

# vim: set expandtab ts=4 ft=bash iskeyword+=\: :