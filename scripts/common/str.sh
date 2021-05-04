function str::is_empty() {
    [[ -z "${1// }" ]]
}

function str::is_not_empty() {
    [[ -n "${1// }" ]]
}

function str::concat() {
    local -n str=$1

    if (( $# == 2 )); then
        local text=$2
        str="${str}${text}"
    else
        local sep="$2"
        local text="$3"
        if [[ -z $str ]]; then
            str="$text"
        else
            IFS="" str="${str}${sep}${text}"
        fi
    fi
}

# vim: set expandtab ts=4 ft=bash iskeyword+=\: :
