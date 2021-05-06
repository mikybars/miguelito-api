import boto3

from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from os import environ as env
from collections import namedtuple
from datetime import datetime

bucket = boto3.resource('s3').Bucket(env['BUCKET_NAME'])
table = boto3.resource('dynamodb').Table(env['TABLE_NAME'])

ShortUrl = namedtuple("ShortUrlBase", ["path", "links_to", "created_at", "user"])


class PathAndUserNotFound(Exception):
    pass


def is_taken(path):
    try:
        bucket.Object(path).load()
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

    bucket.Object(new_url.path).put(WebsiteRedirectLocation=new_url.links_to)
    if user is not None:
        table.put_item(Item=new_url._asdict())

    return new_url


def delete(path, user):
    try:
        table.delete_item(
            Key={'user': user, 'path': path},
            ConditionExpression=Attr('user').exists()
        )
        bucket.Object(path).delete()
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise PathAndUserNotFound
        raise ex
