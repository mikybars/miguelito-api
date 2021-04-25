import api
import boto3, json
from api import s3_client as s3
from botocore.stub import Stubber
from contextlib import contextmanager
from os import environ as env


def request_by_user(user, path):
    return {
        'pathParameters': {
            'path': path
        },
        'requestContext': {
            'authorizer': {
                'claims': {
                    'email': user
                }
            }
        }
    }


def link_by_user(user):
    return {
        'WebsiteRedirectLocation': f'{user}_link',
        'LastModified': '2021-04-19T13:45:01+00:00',
        'Metadata': {
            'user': user
        }
    }


def valid_json(data):
    try:
        json.loads(data)
        return True
    except ValueError:
        return False


@contextmanager
def link_owned_by_user(user):
    with Stubber(s3) as stubber:
        stubber.add_response('head_object', link_by_user(user))
        stubber.add_response('delete_object', {})
        yield stubber


@contextmanager
def link_not_found():
    with Stubber(s3) as stubber:
        stubber.add_client_error('head_object', service_error_code='404')
        yield stubber


@contextmanager
def s3_read_error(code):
    with Stubber(s3) as stubber:
        stubber.add_client_error('head_object', service_error_code=str(code))
        yield stubber


def handle(event):
    response = api.delete_url(event, context={})
    return response['statusCode']


class TestDelete:
    def test_valid_ok_response(self):
        with link_owned_by_user('user1'):
            event = request_by_user('user1', 'path1')

            response = api.delete_url(event, context={})

            assert 'statusCode' in response

    def test_valid_fail_response(self):
        with s3_read_error(500):
            event = request_by_user('user1', 'path1')

            response = api.delete_url(event, context={})

            assert 'statusCode' in response and 'body' in response
            assert valid_json(response['body'])
            assert 'message' in json.loads(response['body'])
            assert 'detail' in json.loads(response['body'])

    def test_link_owned_by_user_gets_deleted(self):
        with link_owned_by_user('user1'):
            event = request_by_user('user1', 'path1')
        
            status = handle(event)

            assert status == 200

    def test_link_not_owned_by_user_returns_forbidden(self):
        with link_owned_by_user('user1'):
            event = request_by_user('user2', 'path1')

            status = handle(event)

            assert status == 403

    def test_link_not_found_returns_forbidden(self):
        with link_not_found():
            event = request_by_user('user1', 'path1')

            status = handle(event)

            assert status == 403

    def test_s3_error_gets_reported(self):
        with s3_read_error(502):
            event = request_by_user('user1', 'path1')

            status = handle(event)

            assert status == 500
