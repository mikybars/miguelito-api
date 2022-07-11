#!/usr/bin/env bash

COMMON_PROMPT_SCRIPT_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
source "${COMMON_PROMPT_SCRIPT_DIR}/style.sh"

PROMPT_SYMBOL="?"

function prompt() {
    # https://stackoverflow.com/a/50281697/13166837
    local -n output=$1
    local text="$2"
    shift 2

    local p="$(style::green ${PROMPT_SYMBOL}) $(style::bold ${text}) "
    echo -n "$p"

    read output

    tput cuu1 && tput el
    echo -n "$p"
    style::blue $output
}

# vim: set expandtab ts=4 ft=bash iskeyword+=\: :
