import json
import logging
import string
import src.repo as repo
import src.http_responses as http

from collections import defaultdict
from random import choice
from itertools import chain
from botocore.exceptions import ClientError
from src.validators import url as validate_url
from src.repo import s3_client


logger = logging.getLogger()


def generate_path(len):
    new_path = ''.join(choice(list(chain(string.ascii_letters, string.digits))) for c in range(len))
    if not repo.find_by_path(new_path):
        return new_path
    return generate_path(len)


def get_body(event):
    return defaultdict(str, json.loads(event['body']))


def get_user(data):
    try:
        return data['requestContext']['authorizer']['claims']['email']
    except KeyError:
       return None


def shorten_url(event, context):
    user = get_user(event)
    body = get_body(event)
    origin_url, custom_path = body['url'].strip(), body['custom_path'].strip()
    
    if not validate_url(origin_url):
        logger.error('URL is invalid')
        return http.bad_request("URL is invalid")

    if not custom_path:
        path = generate_path(7)
    elif not repo.find_by_path(custom_path):
        path = custom_path
    else:
        logger.error(f'Path "/{custom_path}" is already in use')
        return http.bad_request("Path is already in use")

    try:
        return http.ok(repo.save(path, origin_url, user))
    except Exception as ex:
        logger.error(ex)
        if type(ex) == ClientError and ex.response['Error']['Code'] == 'InvalidRedirectLocation':
            return http.bad_request("URL is invalid", ex.response['Error']['Message'])
        else:
            return http.server_error("Error saving redirect", str(ex))


def list_urls(event, context):
    user = get_user(event)
    try:
        return http.ok(repo.find_by_user(user))
    except Exception as ex:
        logger.error(ex)
        return http.server_error("unexpected error", str(ex))


def delete_url(event, context):
    user = get_user(event)
    path = event['pathParameters']['path']

    try:
        url = repo.find_by_path(path)
        if not url or not url.is_owned_by(user):
            return http.forbidden()

        repo.delete(url)
        return http.ok()
    except Exception as ex:
        return http.server_error("unexpected error", str(ex))
