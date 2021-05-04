#!/usr/bin/env bash

# https://letsencrypt.org/es/docs/challenge-types/

function http_01_challenge() {
    local domain token payload

    prompt domain "Domain"
    prompt token "Token: .well-known/acme-challenge/"
    prompt payload "Payload"

    create_website $domain \
        && bind_website_domain_name $domain \
        && upload_file $domain $token $payload

    if prompt_yesno "Create another one?" no; then
        tput cuu1 && tput el
        echo "-------------"
        http_01_challenge
    fi
}

function create_website() {
    local domain=$1

    aws s3api head-bucket --bucket $domain 2>/dev/null \
        || aws s3 mb s3://${domain} >/dev/null
    aws s3 website s3://${domain} \
        --index-document index.html \
        --error-document error.html \
        && log::ok "Website bucket created for domain $(style::blue ${domain})"
}

function bind_website_domain_name() {
    local domain=$1

    local region=$(aws::current_region)
    local root_domain="$(awk -F. '{print $(NF-1)"."$NF}' <<<$domain)"
    local hosted_zone_id=$(aws::get_hosted_zone_id $root_domain)
    str::is_not_empty "$hosted_zone_id" || sys::fail "No hosted zone exists for the given domain"

    local tmp=$(mktemp)

    aws::change_record_set_document_for_website "UPSERT" $domain $region >|$tmp
    aws route53 change-resource-record-sets \
        --hosted-zone-id $hosted_zone_id \
        --change-batch file://$tmp >/dev/null \
        && log::ok "Domain ${domain} linked to website $(style::blue ${domain}.$(aws::s3_website_endpoint $region))"

	rm -f $tmp
}

function upload_file() {
	local domain=$1
	local token=$2
	local payload=$3

    local filename=".well-known/acme-challenge/$token"
	local tmp=$(mktemp)

	cat >|$tmp <<<$payload
	aws s3api put-object \
		--bucket $domain \
		--key $filename \
		--acl public-read \
		--body $tmp >/dev/null \
        && log::ok "File uploaded to $(style::blue http://${domain}/${filename})"

	rm -f $tmp
}

HTTP_01_CHALLENGE_SCRIPT_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
source "${HTTP_01_CHALLENGE_SCRIPT_DIR}/common/aws.sh"
source "${HTTP_01_CHALLENGE_SCRIPT_DIR}/common/log.sh"
source "${HTTP_01_CHALLENGE_SCRIPT_DIR}/common/prompt.sh"
source "${HTTP_01_CHALLENGE_SCRIPT_DIR}/common/str.sh"
source "${HTTP_01_CHALLENGE_SCRIPT_DIR}/common/sys.sh"

http_01_challenge

# vim: set expandtab ts=4 ft=bash iskeyword+=\: :
