import json
import logging
import string
import src.repo as repo

from collections import defaultdict
from random import choice
from itertools import chain
from botocore.exceptions import ClientError
from src.validators import url as validate_url


logger = logging.getLogger()


def generate_path(len):
    new_path = ''.join(choice(list(chain(string.ascii_letters, string.digits))) for c in range(len))
    if not repo.find_by_path(new_path):
        return new_path
    return generate_path(len)


def forbidden():
    return response(403)


def fail(status_code, msg, detail=None):
    return response(status_code, {"message": msg, "detail": detail})


def ok(body=None):
    if body is None:
        return response(200)
    else:
        return response(200, body.to_serializable())


def response(status_code, body=None):
    result = {
        "headers": {
            "Access-Control-Allow-Origin": "*"
        },
        "statusCode": status_code
    }
    if body is not None:
        result['body'] = json.dumps(__new_dict_without_nones(body))

    return result


def __new_dict_without_nones(data):
    return {k: v for k, v in data.items() if v is not None}


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
    if custom_path:
        logger.warning(
            f'Shorten URL: {origin_url} (custom_path="/{custom_path}")')
    else:
        logger.warning(f'Shorten URL: {origin_url}')

    if not validate_url(origin_url):
        logger.error('URL is invalid')
        return fail(400, "URL is invalid")

    if not custom_path:
        path = generate_path(7)
    elif not repo.find_by_path(custom_path):
        path = custom_path
    else:
        logger.error(f'Path "/{custom_path}" is already in use')
        return fail(400, "Path is already in use")

    try:
        return ok(repo.save(path, origin_url, user))
    except Exception as ex:
        logger.error(ex)
        if type(ex) == ClientError and ex.response['Error']['Code'] == 'InvalidRedirectLocation':
            return fail(400, "URL is invalid", ex.response['Error']['Message'])
        else:
            return fail(500, "Error saving redirect", str(ex))


def list_urls(event, context):
    user = get_user(event)
    try:
        return ok(repo.find_by_user(user))
    except Exception as ex:
        logger.error(ex)
        return fail(500, "unexpected error", str(ex))


def delete_url(event, context):
    user = get_user(event)
    path = event['pathParameters']['path']

    try:
        url = repo.find_by_path(path)
        if not url or not url.is_owned_by(user):
            return forbidden()

        repo.delete(url)
        return ok()
    except Exception as ex:
        return fail(500, "unexpected error", str(ex))
