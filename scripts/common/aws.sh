function aws::change_record_set_document_for_website() {
    local action=$1
    local name=$2
    local region=$3
    change_record_set_document_for_alias $action $name "Z1BKCTXD74EZPE" "$(aws::s3_website_endpoint $region)." 
}

function aws::change_record_set_document_for_cloudfront() {
    local action=$1
    local name=$2
    local cloudfront_url=$3
    change_record_set_document_for_alias $action $name "Z2FDTNDATAQYW2" "$cloudfront_url"
}

function change_record_set_document_for_alias() {
    local action=$1
    local name=$2
    local alias_hosted_zone_id=$3
    local dns_name=$4

    cat <<eof
{
    "Changes": [{
        "Action": "$action",
        "ResourceRecordSet": {
            "Name": "${name}.",
            "Type": "A",
            "AliasTarget": {
                "HostedZoneId": "$alias_hosted_zone_id",
                "DNSName": "$dns_name",
                "EvaluateTargetHealth": false
            }}
    }]
}
eof
}

function aws::s3_website_endpoint() {
    local region=$1

    echo "s3-website-${region}.amazonaws.com"
}

function aws::current_region() {
    aws configure get region
}

function aws::get_hosted_zone_id() {
    local domain=$1

    aws route53 list-hosted-zones \
        --query "HostedZones[?Name=='${domain}.'].Id" \
        --output text \
        | awk -F/ '{print $3}'
    # /hostedzone/Z052692033PSFQ78ZCP03
}