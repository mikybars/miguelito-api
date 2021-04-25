import boto3
import json
import logging
import string
from src.validators import url as validate_url
from collections import defaultdict
from random import choice
from itertools import chain
from botocore.exceptions import ClientError
from os import environ as env

s3_client = boto3.client('s3')
logger = logging.getLogger()
bucket_name = env['BUCKET_NAME']


def create_redirect_object(path, origin_url):
    return {
        'Bucket': bucket_name,
        'Key': path,
        'WebsiteRedirectLocation': origin_url
    }


def upload_redirect_object(redirect):
    s3_client.put_object(**redirect)


def is_path_free(path):
    try:
        s3_client.head_object(Bucket=bucket_name, Key=path)
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


def fail(status_code, msg, detail=None):
    return response(status_code, {"message": msg, "detail": detail})


def ok(body):
    if type(body) == str:
        return response(200, {"message": "success", "path": body})
    else:
        return response(200, {"message": "success", "urls": body})


def response(status_code, body):
    return {
        "headers": {
            "Access-Control-Allow-Origin": "*"
        },
        "statusCode": status_code,
        "body": json.dumps(body)
    }


def get_urls_by_user(user):
    return [url for url in all_urls() if url["user"] == user]


def all_urls():
    return (url_details(k) for k in list_bucket())


def list_bucket():
    return (obj['Key'] for obj in s3_client.list_objects(Bucket=bucket_name)['Contents'])


def url_details(path):
    response = s3_client.head_object(Bucket=bucket_name, Key=path)
    return {
        "path": path,
        "url": response.get('WebsiteRedirectLocation'),
        "createdAt": str(response.get('LastModified')),
        "user":  get_user(response)
    }


def get_body(event):
    return defaultdict(str, json.loads(event['body']))


def get_user(data):
    try:
        return data['requestContext']['authorizer']['claims']['email']
    except KeyError:
        try:
            return data['Metadata']['user']
        except KeyError:
            return None


def get_urls(event, context):
    try:
        return ok(get_urls_by_user(get_user(event)))
    except Exception as ex:
        logger.error(ex)
        return fail(500, "unexpected error", str(ex))


def shorten(event, context):
    body = get_body(event)
    origin_url, custom_path = body['url'].strip(), body['custom_path'].strip()
    if custom_path:
        logger.warning(f'Shorten URL: {origin_url} (custom_path="/{custom_path}")')
    else:
        logger.warning(f'Shorten URL: {origin_url}')

    if not validate_url(origin_url):
        logger.error('URL is invalid')
        return fail(400, "URL is invalid")

    if not custom_path:
        path = generate_path(7)
    else:
        if not is_path_free(custom_path):
            logger.error(f'Path "/{custom_path}" is already in use')
            return fail(400, "Path is already in use")
        path = custom_path

    try:
        redirect = create_redirect_object(path, origin_url)
        user = get_user(event)
        if user:
            redirect['Metadata'] = { 'user': user }
        upload_redirect_object(redirect)
        return ok(path)
    except Exception as ex:
        logger.error(ex)
        if type(ex) == ClientError and ex.response['Error']['Code'] == 'InvalidRedirectLocation':
            return fail(400, "URL is invalid", ex.response['Error']['Message'])
        else:
            return fail(500, "Error saving redirect", str(ex))
