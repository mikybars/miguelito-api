from api import s3_client as s3, table as dynamodb
from boto3.dynamodb.conditions import Key
from botocore.stub import Stubber, ANY
from contextlib import contextmanager


@contextmanager
def url_already_existing():
    with Stubber(s3) as stubber:
        stubber.add_response('head_object', {})
        yield stubber


@contextmanager
def url_created_successfully(with_user=False):
    with Stubber(s3) as s3_stubber, Stubber(dynamodb.meta.client) as db_stubber:
        s3_stubber.add_client_error('head_object', service_error_code='404')
        s3_stubber.add_response('put_object', {})
        if with_user:
            db_stubber.add_response('put_item', {})
        yield s3_stubber


@contextmanager
def url_by_user(user, path, links_to):
    with Stubber(dynamodb.meta.client) as db_stubber:
        db_stubber.add_response('query', {
            'Items': [
                {
                    'path': {"S": path},
                    'links_to': {"S": links_to},
                    'created_at': {"S": '2021-04-19T13:45:01+00:00'},
                    'user': {"S": user}
                }
            ]
        }, expected_params={
            'KeyConditionExpression': Key('user').eq(user),
            'TableName': ANY
        })
        yield db_stubber


@contextmanager
def no_urls_by_user(user):
    with Stubber(dynamodb.meta.client) as db_stubber:
        db_stubber.add_response('query', {
            'Items': []
        }, expected_params={
            'KeyConditionExpression': Key('user').eq(user),
            'TableName': ANY
        })
        yield db_stubber


@contextmanager
def delete_path_not_found():
    with Stubber(dynamodb.meta.client) as db_stubber:
        db_stubber.add_client_error('delete_item', service_error_code='ConditionalCheckFailedException')
        yield db_stubber
