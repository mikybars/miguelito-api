#!/usr/bin/env bash

CREATE_TEST_USER_SCRIPT_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
source "${CREATE_TEST_USER_SCRIPT_DIR}/prompt.sh"


function create_test_user() {
    local username password email userpoolid clientid session

    prompt username "Username"
    prompt password "Password"
    prompt email "Email"
    prompt userpoolid "UserPoolId"
    prompt clientid "UserPoolClientId"

    set +x

    echo "Creating user ${username} in the user pool ${userpoolid}"
    aws cognito-idp admin-create-user \
      --user-pool-id ${userpoolid} \
      --username ${username} \
      --temporary-password ${password} \
      --user-attributes Name=given_name,Value=test_user Name=email,Value=${email} >/dev/null \
    && echo "Initiating auth" \
    && session=$(aws cognito-idp initiate-auth \
        --client-id ${clientid} \
        --auth-flow USER_PASSWORD_AUTH \
        --auth-parameters USERNAME=${username},PASSWORD=${password} \
        --output text \
        --query 'Session') \
    && echo "Responding to auth challenge" \
    && idtoken=$(aws cognito-idp respond-to-auth-challenge \
        --client-id ${clientid} \
        --challenge-name NEW_PASSWORD_REQUIRED \
        --challenge-responses "NEW_PASSWORD=${password},USERNAME=${username}" \
        --session "${session}" \
        --output text \
        --query 'AuthenticationResult.IdToken') \
    && echo "IdToken received: ${idtoken}"
}

create_test_user

# vim: set expandtab ts=4 ft=bash :
