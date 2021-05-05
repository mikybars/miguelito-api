from api import s3_client as s3, table as dynamodb
from botocore.stub import Stubber
from contextlib import contextmanager
from os import environ as env


def _link_by_user(user):
    return {
        'WebsiteRedirectLocation': f'{user}_link',
        'LastModified': '2021-04-19T13:45:01+00:00',
        'Metadata': {
            'user': user
        }
    }


def _link_without_user():
    return {
        'WebsiteRedirectLocation': 'https://www.google.com',
        'LastModified': '2021-04-19T13:45:01+00:00'
    }


def _expected_key(key):
    return {
        'Bucket': env['BUCKET_NAME'],
        'Key': key
    }


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
def non_empty_bucket():
    with Stubber(s3) as stubber:
        stubber.add_response('list_objects',
                             {
                                 'Contents': [
                                     {'Key': '0jY7IuW'},
                                     {'Key': '5oPebXc'},
                                     {'Key': 'JRauwqD'}
                                 ]
                             })
        stubber.add_response('head_object', _link_by_user('user1'), _expected_key('0jY7IuW'))
        stubber.add_response('head_object', _link_by_user('user2'), _expected_key('5oPebXc'))
        stubber.add_response('head_object', _link_without_user(), _expected_key('JRauwqD'))
        yield stubber


@contextmanager
def url_owned_by_user(user):
    with Stubber(s3) as stubber:
        stubber.add_response('head_object', _link_by_user(user))
        stubber.add_response('delete_object', {})
        yield stubber


@contextmanager
def url_not_found():
    with Stubber(s3) as stubber:
        stubber.add_client_error('head_object', service_error_code='404')
        yield stubber
