import boto3

from botocore.exceptions import ClientError
from os import environ as env
from collections import namedtuple
from datetime import datetime

BUCKET_NAME = env['BUCKET_NAME']
s3_client = boto3.client('s3')

ShortUrlBase = namedtuple("ShortUrlBase", ["path", "links_to", "created_at", "owner"])


class ShortUrl(ShortUrlBase):
    def is_owned_by(self, user):
        return self.owner == user


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
    result = []
    for key in __list_bucket_keys():
        url = find_by_path(key)
        if url.is_owned_by(user):
            result.append(url)
    return {"urls": result}


def __list_bucket_keys():
    return (obj['Key'] for obj in s3_client.list_objects(Bucket=BUCKET_NAME)['Contents'])


def save(path, links_to, user=None):
    obj = {
        'Bucket': BUCKET_NAME,
        'Key': path,
        'WebsiteRedirectLocation': links_to
    }
    if user is not None:
        obj['Metadata'] = {
            'user': user
        }
    s3_client.put_object(**obj)
    return ShortUrl(path, links_to, str(datetime.now()), user)


def delete(url):
    s3_client.delete_object(Bucket=BUCKET_NAME, Key=url.path)
