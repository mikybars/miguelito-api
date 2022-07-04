import boto3

from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from os import environ as env
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List

bucket = boto3.resource('s3').Bucket(env['BUCKET_NAME'])
table = boto3.resource('dynamodb').Table(env['TABLE_NAME'])


@dataclass
class ShortUrl:
    path: str
    links_to: str
    created_at: str
    updated_at: str = None
    user: str = None

    def asdict(self):
        return asdict(self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})


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


def find_by_user(user) -> Dict[str, List[ShortUrl]]:
    result = table.query(KeyConditionExpression=Key('user').eq(user))
    return {"urls": [ShortUrl(**i).asdict() for i in result['Items']]}


def save(path, links_to, user=None) -> ShortUrl:
    new_url = ShortUrl(path=path, links_to=links_to, created_at=str(datetime.now()), user=user)

    bucket.Object(new_url.path).put(WebsiteRedirectLocation=new_url.links_to)
    if user is not None:
        table.put_item(Item=new_url.asdict())

    return new_url


def delete(path, user) -> None:
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


def get(path, user) -> ShortUrl:
    i = table.get_item(
        Key={'user': user, 'path': path}
    )
    if 'Item' not in i:
        raise PathAndUserNotFound
    return ShortUrl(**(i['Item']))


def update(path, user, data):
    updated_url = get(path, user)
    if 'path' in data:
        delete(path, user)
        updated_url.path = data['path']
    if 'origin' in data:
        updated_url.links_to = data['origin']
        bucket.Object(updated_url.path).put(WebsiteRedirectLocation=updated_url.links_to)
    updated_url.updated_at = str(datetime.now())
    table.put_item(Item=updated_url.asdict())
