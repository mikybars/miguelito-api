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


def s3_delete_object_ok_response(stubber, expected_backhalf):
    stubber.add_response(
        'delete_object',
        {},
        expected_params={
            'Bucket': ANY,
            'Key': expected_backhalf
        }
    )
    return stubber


def db_put_item_new_ok_response(stubber, expected_backhalf, expected_origin, expected_user):
    stubber.add_response(
        'put_item',
        {},
        expected_params={
            'Item': {
                'backhalf': expected_backhalf,
                'origin': expected_origin,
                'created_at': ANY,
                'user': expected_user,
            },
            'TableName': ANY,
            'ConditionExpression': Attr('user').not_exists()
        }
    )
    return stubber


def db_put_item_updated_ok_response(stubber, expected_backhalf, expected_origin, expected_user):
    stubber.add_response(
        'put_item',
        {},
        expected_params={
            'Item': {
                'backhalf': expected_backhalf,
                'origin': expected_origin,
                'created_at': ANY,
                'updated_at': ANY,
                'user': expected_user,
            },
            'TableName': ANY,
            'ConditionExpression': Attr('user').not_exists()
        }
    )
    return stubber


def db_put_item_fail_response(stubber, expected_backhalf, is_update=False):
    expected_item = {
        'backhalf': expected_backhalf,
        'origin': ANY,
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


def db_query_ok_response(stubber, backhalf, url, expected_user):
    stubber.add_response(
        'query',
        {
            'Items': [
                {
                    'backhalf': {"S": backhalf},
                    'origin': {"S": url},
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


def db_delete_item_ok_response(stubber, expected_backhalf):
    stubber.add_response(
        'delete_item',
        {},
        expected_params={
            'Key': {
                'backhalf': expected_backhalf
            },
            'ConditionExpression': ANY,
            'TableName': ANY
        }
    )
    return stubber


def db_delete_item_fail_response(stubber, expected_backhalf, expected_user):
    stubber.add_client_error(
        'delete_item',
        service_error_code='ConditionalCheckFailedException',
        expected_params={
            'Key': {'backhalf': expected_backhalf},
            'ConditionExpression': Attr('user').eq(expected_user),
            'TableName': ANY
        }
    )
    return stubber


def db_get_item_ok_response(stubber, expected_backhalf, origin, user):
    stubber.add_response(
        'get_item',
        {
            'Item': {
                'backhalf': {'S': expected_backhalf},
                'origin': {'S': origin},
                'created_at': {'S': '2021-04-19T13:45:01+00:00'},
                'user': {'S': user}
            }
        },
        expected_params={
            'Key': {
                'backhalf': expected_backhalf
            },
            'TableName': ANY
        }
    )
    return stubber


def db_get_item_not_found(stubber, expected_backhalf):
    stubber.add_response(
        'get_item',
        {},
        expected_params={
            'Key': {
                'backhalf': expected_backhalf
            },
            'TableName': ANY
        }
    )
    return stubber


@contextmanager
def anonymous_link_created_successfully(url):
    with Stubber(s3) as s3_stubber, Stubber(dynamodb) as db_stubber:
        s3_head_object_404_response(s3_stubber)
        s3_put_object_ok_response(s3_stubber, url)
        yield s3_stubber, db_stubber


@contextmanager
def custom_link_created_successfully(url, backhalf, user):
    with Stubber(s3) as s3_stubber, Stubber(dynamodb) as db_stubber:
        db_put_item_new_ok_response(db_stubber, backhalf, url, user)
        s3_put_object_ok_response(s3_stubber, url)
        yield s3_stubber, db_stubber


@contextmanager
def backhalf_already_taken(backhalf):
    with Stubber(dynamodb) as db_stubber:
        yield db_put_item_fail_response(db_stubber, backhalf)


@contextmanager
def link_found_for_user(user, backhalf, origin):
    with Stubber(dynamodb) as db_stubber:
        yield db_query_ok_response(db_stubber, backhalf, origin, user)


@contextmanager
def no_links_found_for_user(user):
    with Stubber(dynamodb) as db_stubber:
        yield db_query_empty_response(db_stubber, user)


@contextmanager
def delete_link_not_found(backhalf, user):
    with Stubber(dynamodb) as db_stubber:
        yield db_delete_item_fail_response(db_stubber, backhalf, user)


@contextmanager
def edit_ok(user, backhalf, origin, new_backhalf, new_origin):
    with Stubber(dynamodb) as db_stubber, Stubber(s3) as s3_stubber:
        db_get_item_ok_response(db_stubber, backhalf, origin, user)
        db_put_item_updated_ok_response(db_stubber, new_backhalf, new_origin, user)
        db_delete_item_ok_response(db_stubber, backhalf)
        s3_delete_object_ok_response(s3_stubber, backhalf)
        s3_put_object_ok_response(s3_stubber, new_origin)
        yield s3_stubber, db_stubber


@contextmanager
def link_not_found(backhalf):
    with Stubber(dynamodb) as db_stubber:
        yield db_get_item_not_found(db_stubber, backhalf)


@contextmanager
def link_owned_by_user(backhalf, origin, user):
    with Stubber(dynamodb) as db_stubber:
        yield db_get_item_ok_response(db_stubber, backhalf, origin, user)


@contextmanager
def duplicate_backhalf_edit_error(backhalf, origin, user, new_backhalf):
    with Stubber(dynamodb) as db_stubber:
        db_get_item_ok_response(db_stubber, backhalf, origin, user)
        db_put_item_fail_response(db_stubber, new_backhalf, is_update=True)
        yield db_stubber
