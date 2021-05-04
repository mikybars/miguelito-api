COLOR_RED="1"
COLOR_GREEN="2"
COLOR_YELLOW="3"
COLOR_BLUE="6"
COLOR_GREY="8"

function style::red() {
    term::colorize $COLOR_RED $*
}

function style::green() {
    term::colorize $COLOR_GREEN $*
}

function style::blue() {
    term::colorize $COLOR_BLUE $*
}

function style::yellow() {
    term::colorize $COLOR_YELLOW $*
}

function style::dim() {
    term::colorize $COLOR_GREY $*
}

function style::bold() {
    if term::no_color; then
        echo $*;
    else
        echo $(tput bold)$*$(tput sgr0)
    fi
}

function term::colorize() {
    local code=$1
    shift

    if term::no_color; then
        echo $*
    else
        echo $(tput setaf $code)$*$(tput sgr0)
    fi
}

function term::no_color() {
    # https://stackoverflow.com/a/13864829/13166837
    [[ -n ${NO_COLOR+x} ]]
}

# vim: set expandtab ts=4 ft=bash iskeyword+=\: :