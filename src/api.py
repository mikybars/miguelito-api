import boto3
import json
import logging
import string
from collections import defaultdict
from random import choice
from itertools import chain
from urllib.parse import urlparse
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


def invalid_url(url):
    url_parsed = urlparse(url)
    return not all([url_parsed.scheme, url_parsed.netloc, url_parsed.path])


def extract_url(event):
    body = defaultdict(str, json.loads(event['body']))
    return body['url']


def handle(event, context):
    load_config()
    origin_url = extract_url(event)
    logger.warning(f'Received url shorten request for {origin_url}')

    if not origin_url.strip():
        logger.error('URL is empty or missing')
        return build_response(400, "URL is required")

    if invalid_url(origin_url):
        logger.error('URL is invalid')
        return build_response(400, "URL is invalid")

    try:
        path = generate_path(7)
        save_redirect(build_redirect(path, origin_url))
        return build_response(200, "success", path)
    except Exception as ex:
        logger.error(ex)
        return build_response(500, "Error saving redirect")
