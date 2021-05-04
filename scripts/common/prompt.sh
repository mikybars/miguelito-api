#!/usr/bin/env bash

COMMON_PROMPT_SCRIPT_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
source "${COMMON_PROMPT_SCRIPT_DIR}/term.sh"
source "${COMMON_PROMPT_SCRIPT_DIR}/str.sh"
source "${COMMON_PROMPT_SCRIPT_DIR}/sys.sh"

PROMPT_SYMBOL="?"

function prompt() {
    # https://stackoverflow.com/a/50281697/13166837
    local -n output=$1
    local text="$2"
    shift 2

    local p="$(style::green ${PROMPT_SYMBOL}) $(style::bold ${text}) "
    echo -n "$p"

    if (( $# > 0 )); then
        local default=$1
        echo -n "$(style::dim \(${default}\)) "
    fi

    read output
    if str::is_empty "$output" && [[ -n $default ]]; then
        output=$default
    fi

    tput cuu1 && tput el
    echo -n "$p"
    style::blue $output
}

function prompt_choice() {
    sys::require_command "simple-term-menu" "https://pypi.org/project/simple-term-menu/"

    local -n output=$1
    local text="$2"
    shift 2
    local choices=($*)

    i=$(simple-term-menu --stdout --title "${PROMPT_SYMBOL} ${text}" ${choices[@]})
    output=${choices[((i-1))]}
}

function prompt_multiple_choices() {
    sys::require_command "simple-term-menu" "https://pypi.org/project/simple-term-menu/"

    local -n output=$1
    local text="$2"
    shift 2
    local choices=($*)

    idxs=$(simple-term-menu \
        --stdout \
        --multi-select \
        --show-multi-select-hint \
        --title "${PROMPT_SYMBOL} ${text}" ${choices[@]})

    output=""
    IFS=,
    for i in $idxs; do
        local selected_item="${choices[((i-1))]}"
        str::concat output "," "$selected_item"
    done
}

function prompt_yesno() {
    local text="$1"
    local default="yes"

    if (( $# > 1 )); then
        default=$2
    fi

    local p="$(style::green ${PROMPT_SYMBOL}) $(style::bold ${text}) "
    echo -n "$p"

    if is_yes $default; then
        echo -n "$(style::dim \(Y/n\)) "
    else
        echo -n "$(style::dim \(y/N\)) "
    fi

    read output
    is_yes $output || (str::is_empty "$output" && is_yes $default)
}

function is_yes() {
    [[ $1 =~ ^(y|Y|yes|YES)$ ]]
}

# vim: set expandtab ts=4 ft=bash iskeyword+=\: :
