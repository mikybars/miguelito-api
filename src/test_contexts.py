from contextlib import contextmanager

from boto3.dynamodb.conditions import Key
from botocore.stub import Stubber, ANY

from api import repo

s3 = repo.bucket.meta.client
dynamodb = repo.table.meta.client


@contextmanager
def path_already_taken(path):
    with Stubber(dynamodb) as db_stubber:
        db_stubber.add_client_error('put_item', service_error_code='ConditionalCheckFailedException')
        yield db_stubber


@contextmanager
def url_created_successfully():
    with Stubber(s3) as s3_stubber, Stubber(dynamodb) as db_stubber:
        s3_stubber.add_client_error('head_object', service_error_code='404')
        s3_stubber.add_response('put_object', {})
        yield s3_stubber, db_stubber


@contextmanager
def custom_url_created_successfully():
    with Stubber(s3) as s3_stubber, Stubber(dynamodb) as db_stubber:
        db_stubber.add_response('put_item', {})
        s3_stubber.add_response('put_object', {})
        yield s3_stubber, db_stubber


@contextmanager
def url_found_for_user(user, path, links_to):
    with Stubber(dynamodb) as db_stubber:
        db_stubber.add_response(
            'query',
            {
                'Items': [
                    {
                        'path': {"S": path},
                        'links_to': {"S": links_to},
                        'created_at': {"S": '2021-04-19T13:45:01+00:00'},
                        'user': {"S": user}
                    }
                ]
            },
            expected_params={
                'IndexName': 'User-index',
                'KeyConditionExpression': Key('user').eq(user),
                'TableName': ANY
            })
        yield db_stubber


@contextmanager
def no_urls_found_for_user(user):
    with Stubber(dynamodb) as db_stubber:
        db_stubber.add_response(
            'query',
            {'Items': []},
            expected_params={
                'IndexName': 'User-index',
                'KeyConditionExpression': Key('user').eq(user),
                'TableName': ANY
            })
        yield db_stubber


@contextmanager
def delete_path_not_found(path, user):
    with Stubber(dynamodb) as db_stubber:
        db_stubber.add_client_error(
            'delete_item',
            service_error_code='ConditionalCheckFailedException',
            expected_params={
                'Key': {'path': path},
                'ConditionExpression': ANY,
                'TableName': ANY
            })
        yield db_stubber


@contextmanager
def edit_ok(user, path, origin, new_path, new_origin):
    with Stubber(dynamodb) as db_stubber, Stubber(s3) as s3_stubber:
        db_stubber.add_response(
            'get_item',
            {
                'Item': {
                    'path': {'S': path},
                    'links_to': {'S': origin},
                    'created_at': {'S': '2021-04-19T13:45:01+00:00'},
                    'user': {'S': user}
                }
            },
            expected_params={
                'Key': {
                    'path': path
                },
                'TableName': ANY
            })
        db_stubber.add_response(
            'put_item',
            {},
            expected_params={
                'Item': {
                    'path': new_path,
                    'links_to': new_origin,
                    'created_at': ANY,
                    'updated_at': ANY,
                    'user': user
                },
                'TableName': ANY
            }
        )
        db_stubber.add_response(
            'delete_item',
            {},
            expected_params={
                'Key': {
                    'path': path
                },
                'ConditionExpression': ANY,
                'TableName': ANY
            }
        )
        s3_stubber.add_response(
            'delete_object',
            {},
            expected_params={
                'Bucket': ANY,
                'Key': path
            }
        )
        s3_stubber.add_response(
            'put_object',
            {},
            expected_params={
                'Bucket': ANY,
                'Key': new_path,
                'WebsiteRedirectLocation': new_origin
            }
        )
        yield s3_stubber, db_stubber


@contextmanager
def path_not_found(path):
    with Stubber(dynamodb) as db_stubber:
        db_stubber.add_response(
            'get_item',
            {},
            expected_params={
                'Key': {
                    'path': path
                },
                'TableName': ANY
            })
        yield db_stubber


@contextmanager
def path_owned_by_user(path, user):
    with Stubber(dynamodb) as db_stubber:
        db_stubber.add_response(
            'get_item',
            {
                'Item': {
                    'path': {'S': path},
                    'links_to': {'S': 'https://www.google.com'},
                    'created_at': {'S': '2021-04-19T13:45:01+00:00'},
                    'user': {'S': user}
                }
            },
            expected_params={
                'Key': {
                    'path': path
                },
                'TableName': ANY
            })
        yield db_stubber


@contextmanager
def duplicate_path_edit_error(path, user, new_path):
    with Stubber(dynamodb) as db_stubber:
        db_stubber.add_response(
            'get_item',
            {
                'Item': {
                    'path': {"S": path},
                    'links_to': {"S": 'https://www.google.com'},
                    'created_at': {"S": '2021-04-19T13:45:01+00:00'},
                    'user': {"S": user}
                }
            },
            expected_params={
                'Key': {
                    'path': path
                },
                'TableName': ANY
            })
        db_stubber.add_client_error(
            'put_item',
            service_error_code='ConditionalCheckFailedException',
            expected_params={
                'Item': {
                    'path': new_path,
                    'links_to': ANY,
                    'created_at': ANY,
                    'updated_at': ANY,
                    'user': user
                },
                'TableName': ANY
            }
        )
        yield db_stubber
