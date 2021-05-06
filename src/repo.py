import boto3

from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from os import environ as env
from collections import namedtuple
from datetime import datetime

BUCKET_NAME = env['BUCKET_NAME']
s3_client = boto3.client('s3')
table = boto3.resource('dynamodb').Table(env['TABLE_NAME'])

ShortUrl = namedtuple("ShortUrlBase", ["path", "links_to", "created_at", "user"])


class PathAndUserNotFound(Exception):
    pass


def is_taken(path):
    try:
        s3_client.head_object(Bucket=BUCKET_NAME, Key=path)
        return True
    except ClientError as ex:
        if ex.response['Error']['Code'] == '404':
            return False
        raise ex


def find_by_user(user):
    result = table.query(KeyConditionExpression=Key('user').eq(user))
    return {"urls": [ShortUrl(**i) for i in result['Items']]}


def save(path, links_to, user=None):
    new_url = ShortUrl(path, links_to, str(datetime.now()), user)
    obj = {
        'Bucket': BUCKET_NAME,
        'Key': path,
        'WebsiteRedirectLocation': links_to
    }
    if user is not None:
        table.put_item(Item=new_url._asdict())
    s3_client.put_object(**obj)
    return new_url


def delete(path, user):
    try:
        table.delete_item(
            Key={'user': user, 'path': path},
            ConditionExpression=Attr('user').exists()
        )
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=path)
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise PathAndUserNotFound
        raise ex
