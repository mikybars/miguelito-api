#!/usr/bin/env bash

function clean_challenge_websites() {
    local domain hosted_zone_id

    if (( $# > 0 )); then
        hosted_zone_id=$1
    else
        prompt domain "Root Domain"

        log::info "🔎 Looking up hosted zone..."
        hosted_zone_id=$(aws::get_hosted_zone_id $domain)
        str::is_not_empty "$hosted_zone_id" || sys::fail "No hosted zone exists for the given domain"
    fi

    log::info "🔎 Finding buckets..."
    local buckets
    buckets=$(list_website_buckets $hosted_zone_id)

    log::info "🔎 Filtering challenge buckets..."
    buckets=$(filter_challenge_buckets $buckets)
    str::is_not_empty "$buckets" || sys::warn_and_exit "No website buckets in the hosted zone"

    local selected_buckets
    prompt_multiple_choices selected_buckets "Choose website" $buckets
    IFS=","
    for b in $selected_buckets; do
        delete_domain_alias $hosted_zone_id $b \
            && permanently_delete_bucket $b
    done; 
    unset IFS

    if prompt_yesno "Delete another one?"; then
        clean_challenge_websites $hosted_zone_id
    fi
}

function list_website_buckets() {
    local hosted_zone_id=$1
    local region=$(aws::current_region)

    aws route53 list-resource-record-sets \
        --hosted-zone-id $hosted_zone_id \
        --query "ResourceRecordSets[?AliasTarget.DNSName=='s3-website-${region}.amazonaws.com.'].Name" \
        --output text\
        | xargs -n 1 | sed 's/\.$//'
}

function filter_challenge_buckets() {
    for b in $*; do
        aws s3api list-objects \
            --bucket $b \
            --query "Contents[].Key" \
            --output text \
            | grep -qve '^.well-known/acme-challenge' \
            || echo $b
    done
}

function delete_domain_alias() {
    local hosted_zone_id=$1
    local name=$2

    local tmp=$(mktemp)

    aws::change_record_set_document_for_website "DELETE" $name $(aws::current_region) >|$tmp
    aws route53 change-resource-record-sets \
        --hosted-zone-id $hosted_zone_id \
        --change-batch file://$tmp >/dev/null \
        && log::ok "Domain name $(style::blue ${name}) successfully deleted"

    rm -f $tmp
}

function permanently_delete_bucket() {
    local bucket=$1

    aws s3 rm s3://${bucket} --recursive >/dev/null \
        && aws s3 rb s3://${bucket} >/dev/null \
        && log::ok "Bucket $(style::blue ${bucket}) successfully deleted"
}

CLEAN_CHALLENGE_WEBSITES_SCRIPT_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
source "${CLEAN_CHALLENGE_WEBSITES_SCRIPT_DIR}/common/aws.sh"
source "${CLEAN_CHALLENGE_WEBSITES_SCRIPT_DIR}/common/log.sh"
source "${CLEAN_CHALLENGE_WEBSITES_SCRIPT_DIR}/common/prompt.sh"
source "${CLEAN_CHALLENGE_WEBSITES_SCRIPT_DIR}/common/str.sh"
source "${CLEAN_CHALLENGE_WEBSITES_SCRIPT_DIR}/common/sys.sh"

clean_challenge_websites

# vim: set expandtab ts=4 ft=bash iskeyword+=\: :
