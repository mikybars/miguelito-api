#!/usr/bin/env bash

function bind_user_pool_domain() {
    local auth_domain root_domain

    prompt auth_domain "Auth domain"
    root_domain="$(awk -F. '{print $(NF-1)"."$NF}' <<<$auth_domain)"

    local hosted_zone_id=$(aws::get_hosted_zone_id $root_domain)
    str::is_not_empty "$hosted_zone_id" || sys::fail "No hosted zone exists for the given domain"

    local cloudfront_url=$(get_userpool_distribution $auth_domain)

    local tmp=$(mktemp)

    aws::change_record_set_document_for_cloudfront "UPSERT" "$auth_domain" "$cloudfront_url" >|$tmp
    aws route53 change-resource-record-sets \
        --hosted-zone-id $hosted_zone_id \
        --change-batch file://$tmp >/dev/null \
        &&  log::ok "Domain $auth_domain bound to distribution $(style::blue $cloudfront_url)"

    rm -f $tmp
}

function get_userpool_distribution() {
    local auth_domain=$1

    aws cognito-idp describe-user-pool-domain \
            --domain $auth_domain \
            --output text \
            --query "DomainDescription.CloudFrontDistribution"
}


BIND_USER_POOL_SCRIPT_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
source "${BIND_USER_POOL_SCRIPT_DIR}/common/aws.sh"
source "${BIND_USER_POOL_SCRIPT_DIR}/common/log.sh"
source "${BIND_USER_POOL_SCRIPT_DIR}/common/prompt.sh"
source "${BIND_USER_POOL_SCRIPT_DIR}/common/str.sh"
source "${BIND_USER_POOL_SCRIPT_DIR}/common/sys.sh"

bind_user_pool_domain
