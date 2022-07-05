import boto3

from src.shorturl import ShortUrl
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from os import environ as env
from datetime import datetime
from typing import Dict, List


bucket = boto3.resource('s3').Bucket(env['BUCKET_NAME'])
table = boto3.resource('dynamodb').Table(env['TABLE_NAME'])


class DuplicateKey(Exception):
    pass


class KeyNotFound(Exception):
    pass


def is_taken(path):
    try:
        bucket.Object(path).load()
        return True
    except ClientError as ex:
        if ex.response['Error']['Code'] == '404':
            return False
        raise ex


def find_by_user(user: str) -> List[ShortUrl]:
    result = table.query(
        IndexName='User-index',
        KeyConditionExpression=Key('user').eq(user),
    )
    return [ShortUrl(**i) for i in result['Items']]


def save(new_url: ShortUrl) -> ShortUrl:
    try:
        if new_url.user is not None:
            table.put_item(
                Item=new_url.asdict(),
                ConditionExpression=Attr('user').not_exists()
            )
        bucket.Object(new_url.path).put(WebsiteRedirectLocation=new_url.links_to)
        return new_url
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise DuplicateKey
        raise ex


def delete(path: str, user: str) -> None:
    try:
        table.delete_item(
            Key={
                'path': path
            },
            ConditionExpression=Attr('user').eq(user)
        )
        bucket.Object(path).delete()
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise KeyNotFound
        raise ex


def update(path: str, user: str, data: Dict) -> ShortUrl:
    updated_url = get(path)
    if updated_url.user != user:
        raise KeyNotFound
    try:
        if 'path' in data:
            updated_url.path = data['path']
        if 'origin' in data:
            updated_url.links_to = data['origin']
        updated_url.updated_at = str(datetime.now())
        table.put_item(
            Item=updated_url.asdict()
        )
        if 'path' in data:
            delete(path, user)
        if 'origin' in data:
            bucket.Object(updated_url.path).put(WebsiteRedirectLocation=updated_url.links_to)
        return updated_url
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise DuplicateKey


def get(path: str) -> ShortUrl:
    i = table.get_item(
        Key={
            'path': path
        }
    )
    if 'Item' not in i:
        raise KeyNotFound
    return ShortUrl(**(i['Item']))
