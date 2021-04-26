import json
import logging
import string
import src.repo as repo
import src.http_responses as http

from collections import defaultdict
from random import choice
from itertools import chain
from botocore.exceptions import ClientError
from src.validators import url as is_valid_url
from src.repo import s3_client


logger = logging.getLogger()

class ValidationError(Exception):
    pass


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


def validate_url(url):
    if not is_valid_url(url):
        raise ValidationError("URL is invalid")


def validate_custom_path(path):
    if path and repo.find_by_path(path):
        raise ValidationError("Path is already in use")


def shorten_url(event, context):
    user = get_user(event)
    body = get_body(event)
    url, path = body['url'].strip(), body['custom_path'].strip()

    try:
        validate_url(url)
        validate_custom_path(path)

        if not path:
            path = generate_path(len=7)
        
        return http.ok(repo.save(path, url, user))
    except ValidationError as ex:
        logger.error(ex)
        return http.bad_request(str(ex))
    except Exception as ex:
        logger.error(ex)
        if type(ex) == ClientError and ex.response['Error']['Code'] == 'InvalidRedirectLocation':
            return http.bad_request("URL is invalid", ex.response['Error']['Message'])
        else:
            return http.server_error("unexpected error", str(ex))


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
