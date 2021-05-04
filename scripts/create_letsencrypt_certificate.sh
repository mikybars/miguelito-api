#!/usr/bin/env bash

function create_letsencrypt_certificate() {
    sys::require_command certbot "https://certbot.eff.org/docs/install.html"

    local working_dir maintainer domains

    prompt working_dir "Working dir" "./letsencrypt"
    mkdir -p $working_dir || exit $?

    if git::is_inside_repo; then
        local user_email=$(git::get_user_email)
        prompt maintainer "Maintainer email" $user_email
    else
        prompt maintainer "Maintainer email"
    fi

    prompt domains "Domain (Subject CN)"
    while true; do
        local alt_domain
        prompt alt_domain "Other domain (Subject Alternative Name)" "end"

        [[ $alt_domain == end ]] && break

        str::concat domains "," $alt_domain
    done

    invoke_certbot $working_dir $maintainer $domains
}

function invoke_certbot() {
    local working_dir=$1
    local maintainer=$2
    local domains=$3

    certbot certonly \
        --config-dir "$working_dir" \
        --work-dir "$working_dir" \
        --logs-dir "$working_dir" \
        --manual \
        --agree-tos \
        --email $maintainer\
        -d $domains
}

CREATE_CERTIFICATE_SCRIPT_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
source "${CREATE_CERTIFICATE_SCRIPT_DIR}/common/prompt.sh"
source "${CREATE_CERTIFICATE_SCRIPT_DIR}/common/sys.sh"
source "${CREATE_CERTIFICATE_SCRIPT_DIR}/common/str.sh"
source "${CREATE_CERTIFICATE_SCRIPT_DIR}/common/git.sh"

create_letsencrypt_certificate

# vim: set expandtab ts=4 ft=bash iskeyword+=\: :