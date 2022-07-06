from api import repo
from boto3.dynamodb.conditions import Key, Attr
from botocore.stub import Stubber, ANY
from contextlib import contextmanager

s3 = repo.bucket.meta.client
dynamodb = repo.table.meta.client


def s3_put_object_ok_response(stubber, url):
    stubber.add_response(
        'put_object',
        {},
        expected_params={
            'Bucket': ANY,
            'Key': ANY,
            'WebsiteRedirectLocation': url
        }
    )
    return stubber


def s3_head_object_404_response(stubber):
    stubber.add_client_error(
        'head_object',
        service_error_code='404'
    )
    return stubber


def s3_delete_object_ok_response(stubber, expected_path):
    stubber.add_response(
        'delete_object',
        {},
        expected_params={
            'Bucket': ANY,
            'Key': expected_path
        }
    )
    return stubber


def db_put_item_new_ok_response(stubber, expected_path, expected_url, expected_user):
    stubber.add_response(
        'put_item',
        {},
        expected_params={
            'Item': {
                'path': expected_path,
                'links_to': expected_url,
                'created_at': ANY,
                'user': expected_user,
            },
            'TableName': ANY,
            'ConditionExpression': Attr('user').not_exists()
        }
    )
    return stubber


def db_put_item_updated_ok_response(stubber, expected_path, expected_url, expected_user):
    stubber.add_response(
        'put_item',
        {},
        expected_params={
            'Item': {
                'path': expected_path,
                'links_to': expected_url,
                'created_at': ANY,
                'updated_at': ANY,
                'user': expected_user,
            },
            'TableName': ANY,
            'ConditionExpression': Attr('user').not_exists()
        }
    )
    return stubber


def db_put_item_fail_response(stubber, expected_path, is_update=False):
    expected_item = {
        'path': expected_path,
        'links_to': ANY,
        'created_at': ANY,
        'user': ANY
    }
    if is_update:
        expected_item['updated_at'] = ANY
    stubber.add_client_error(
        'put_item',
        service_error_code='ConditionalCheckFailedException',
        expected_params={
            'Item': expected_item,
            'ConditionExpression': Attr('user').not_exists(),
            'TableName': ANY
        }
    )
    return stubber


def db_query_ok_response(stubber, path, url, expected_user):
    stubber.add_response(
        'query',
        {
            'Items': [
                {
                    'path': {"S": path},
                    'links_to': {"S": url},
                    'created_at': {"S": '2021-04-19T13:45:01+00:00'},
                    'user': {"S": expected_user}
                }
            ]
        },
        expected_params={
            'IndexName': 'User-index',
            'KeyConditionExpression': Key('user').eq(expected_user),
            'TableName': ANY
        }
    )
    return stubber


def db_query_empty_response(stubber, expected_user):
    stubber.add_response(
        'query',
        {'Items': []},
        expected_params={
            'IndexName': 'User-index',
            'KeyConditionExpression': Key('user').eq(expected_user),
            'TableName': ANY
        }
    )
    return stubber


def db_delete_item_ok_response(stubber, expected_path):
    stubber.add_response(
        'delete_item',
        {},
        expected_params={
            'Key': {
                'path': expected_path
            },
            'ConditionExpression': ANY,
            'TableName': ANY
        }
    )
    return stubber


def db_delete_item_fail_response(stubber, expected_path, expected_user):
    stubber.add_client_error(
        'delete_item',
        service_error_code='ConditionalCheckFailedException',
        expected_params={
            'Key': {'path': expected_path},
            'ConditionExpression': Attr('user').eq(expected_user),
            'TableName': ANY
        }
    )
    return stubber


def db_get_item_ok_response(stubber, expected_path, origin, user):
    stubber.add_response(
        'get_item',
        {
            'Item': {
                'path': {'S': expected_path},
                'links_to': {'S': origin},
                'created_at': {'S': '2021-04-19T13:45:01+00:00'},
                'user': {'S': user}
            }
        },
        expected_params={
            'Key': {
                'path': expected_path
            },
            'TableName': ANY
        }
    )
    return stubber


def db_get_item_not_found(stubber, expected_path):
    stubber.add_response(
        'get_item',
        {},
        expected_params={
            'Key': {
                'path': expected_path
            },
            'TableName': ANY
        }
    )
    return stubber


@contextmanager
def anonymous_url_created_successfully(url):
    with Stubber(s3) as s3_stubber, Stubber(dynamodb) as db_stubber:
        s3_head_object_404_response(s3_stubber)
        s3_put_object_ok_response(s3_stubber, url)
        yield s3_stubber, db_stubber


@contextmanager
def custom_url_created_successfully(url, path, user):
    with Stubber(s3) as s3_stubber, Stubber(dynamodb) as db_stubber:
        db_put_item_new_ok_response(db_stubber, path, url, user)
        s3_put_object_ok_response(s3_stubber, url)
        yield s3_stubber, db_stubber


@contextmanager
def path_already_taken(path):
    with Stubber(dynamodb) as db_stubber:
        yield db_put_item_fail_response(db_stubber, path)


@contextmanager
def url_found_for_user(user, path, links_to):
    with Stubber(dynamodb) as db_stubber:
        yield db_query_ok_response(db_stubber, path, links_to, user)


@contextmanager
def no_urls_found_for_user(user):
    with Stubber(dynamodb) as db_stubber:
        yield db_query_empty_response(db_stubber, user)


@contextmanager
def delete_path_not_found(path, user):
    with Stubber(dynamodb) as db_stubber:
        yield db_delete_item_fail_response(db_stubber, path, user)


@contextmanager
def edit_ok(user, path, origin, new_path, new_origin):
    with Stubber(dynamodb) as db_stubber, Stubber(s3) as s3_stubber:
        db_get_item_ok_response(db_stubber, path, origin, user)
        db_put_item_updated_ok_response(db_stubber, new_path, new_origin, user)
        db_delete_item_ok_response(db_stubber, path)
        s3_delete_object_ok_response(s3_stubber, path)
        s3_put_object_ok_response(s3_stubber, new_origin)
        yield s3_stubber, db_stubber


@contextmanager
def path_not_found(path):
    with Stubber(dynamodb) as db_stubber:
        yield db_get_item_not_found(db_stubber, path)


@contextmanager
def path_owned_by_user(path, origin, user):
    with Stubber(dynamodb) as db_stubber:
        yield db_get_item_ok_response(db_stubber, path, origin, user)


@contextmanager
def duplicate_path_edit_error(path, origin, user, new_path):
    with Stubber(dynamodb) as db_stubber:
        db_get_item_ok_response(db_stubber, path, origin, user)
        db_put_item_fail_response(db_stubber, new_path, is_update=True)
        yield db_stubber
