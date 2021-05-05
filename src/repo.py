import boto3

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from os import environ as env
from collections import namedtuple
from datetime import datetime

BUCKET_NAME = env['BUCKET_NAME']
s3_client = boto3.client('s3')
table = boto3.resource('dynamodb').Table(env['TABLE_NAME'])

ShortUrlBase = namedtuple("ShortUrlBase", ["path", "links_to", "created_at", "user"])


class ShortUrl(ShortUrlBase):
    def is_owned_by(self, user):
        return self.user == user


def find_by_path(path):
    try:
        response = s3_client.head_object(Bucket=BUCKET_NAME, Key=path)
        links_to = response.get('WebsiteRedirectLocation')
        created_at = response.get('LastModified')
        owner = response.get('Metadata', {}).get('user')
        return ShortUrl(path, links_to, str(created_at), owner)
    except ClientError as ex:
        if ex.response['Error']['Code'] == '404':
            return None
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


def delete(url):
    s3_client.delete_object(Bucket=BUCKET_NAME, Key=url.path)
