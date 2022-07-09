import boto3

from src.link import Link
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


def is_taken(backhalf):
    try:
        bucket.Object(backhalf).load()
        return True
    except ClientError as ex:
        if ex.response['Error']['Code'] == '404':
            return False
        raise ex


def find_by_user(user: str) -> List[Link]:
    result = table.query(
        IndexName='User-index',
        KeyConditionExpression=Key('user').eq(user),
    )
    return [Link(**i) for i in result['Items']]


def save(new_link: Link) -> Link:
    try:
        if new_link.user is not None:
            table.put_item(
                Item=new_link.asdict(),
                ConditionExpression=Attr('user').not_exists()
            )
        bucket.Object(new_link.backhalf).put(WebsiteRedirectLocation=new_link.origin)
        return new_link
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise DuplicateKey
        raise ex


def delete(backhalf: str, user: str) -> None:
    try:
        table.delete_item(
            Key={
                'backhalf': backhalf
            },
            ConditionExpression=Attr('user').eq(user)
        )
        bucket.Object(backhalf).delete()
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise KeyNotFound
        raise ex


def update(backhalf: str, user: str, data: Dict) -> Link:
    updated_link = get(backhalf)
    if updated_link.user != user:
        raise KeyNotFound
    try:
        if 'backhalf' in data:
            updated_link.backhalf = data['backhalf']
        if 'origin' in data:
            updated_link.origin = data['origin']
        updated_link.updated_at = str(datetime.now())
        table.put_item(
            Item=updated_link.asdict(),
            ConditionExpression=Attr('user').not_exists()
        )
        if 'backhalf' in data:
            delete(backhalf, user)
        if 'origin' in data:
            bucket.Object(updated_link.backhalf).put(WebsiteRedirectLocation=updated_link.origin)
        return updated_link
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise DuplicateKey


def get(backhalf: str) -> Link:
    i = table.get_item(
        Key={
            'backhalf': backhalf
        }
    )
    if 'Item' not in i:
        raise KeyNotFound
    return Link(**(i['Item']))
