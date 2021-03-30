import boto3
import json
import logging
import string
from src.validators import url as validate_url
from collections import defaultdict
from random import choice
from itertools import chain
from botocore.exceptions import ClientError

config = dict()
s3_client = boto3.client('s3')
logger = logging.getLogger()


def load_config():
    global config
    with open('config.json') as f:
        config = json.load(f)


def build_redirect(path, origin_url=None):
    redirect = {
        'Bucket': config['bucket'],
        'Key': path
    }
    if origin_url:
        redirect['WebsiteRedirectLocation'] = origin_url
    return redirect


def save_redirect(redirect):
    s3_client.put_object(**redirect)


def is_path_free(path):
    try:
        s3_client.head_object(**build_redirect(path))
        return False
    except ClientError as ex:
        error_code = ex.response['Error']['Code']
        if error_code == '404':
            return True
        raise ex


def generate_path(len):
    new_path = ''.join(choice(list(chain(string.ascii_letters, string.digits))) for c in range(len))
    if is_path_free(new_path):
        return new_path
    return generate_path(len)


def build_response(status_code, msg, path=None):
    body = {
        "message": msg
    }
    if path:
        body['path'] = path
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }


def get_body(event):
    return defaultdict(str, json.loads(event['body']))


def handle(event, context):
    load_config()

    body = get_body(event)
    origin_url, custom_path = body['url'].strip(), body['custom_path'].strip()
    if custom_path:
        logger.warning(f'Shorten URL: {origin_url} (custom_path="/{custom_path}")')
    else:
        logger.warning(f'Shorten URL: {origin_url}')

    if not origin_url:
        logger.error('URL is empty or missing')
        return build_response(400, "URL is required")

    if not validate_url(origin_url):
        logger.error('URL is invalid')
        return build_response(400, "URL is invalid")

    if not custom_path:
        path = generate_path(7)
    else:
        if not is_path_free(custom_path):
            logger.error(f'Path "/{custom_path}" is already in use')
            return build_response(400, "Path is already in use")
        path = custom_path

    try:
        save_redirect(build_redirect(path, origin_url))
        return build_response(200, "success", path)
    except Exception as ex:
        logger.error(ex)
        return build_response(500, "Error saving redirect")
