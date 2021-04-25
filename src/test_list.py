import api
import boto3, json
from api import s3_client as s3
from botocore.stub import Stubber
from contextlib import contextmanager
from os import environ as env


def request_by_user(user):
    return {
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


def link_without_user():
    return {
        'WebsiteRedirectLocation': 'https://www.google.com',
        'LastModified': '2021-04-19T13:45:01+00:00'
    }


def expected_key(key):
    return {
        'Bucket': env['BUCKET_NAME'],
        'Key': key
    }


def valid_json(data):
    try:
        json.loads(data)
        return True
    except ValueError:
        return False


@contextmanager
def non_empty_bucket():
    with Stubber(s3) as stubber:
        stubber.add_response('list_objects', 
        {
            'Contents': [
                { 'Key': '0jY7IuW' },
                { 'Key': '5oPebXc' },
                { 'Key': 'JRauwqD' }
            ]
        })
        stubber.add_response('head_object', link_by_user('user1'), expected_key('0jY7IuW'))
        stubber.add_response('head_object', link_by_user('user2'), expected_key('5oPebXc'))
        stubber.add_response('head_object', link_without_user(), expected_key('JRauwqD'))
        yield stubber


@contextmanager
def s3_read_error(code):
    with Stubber(s3) as stubber:
        stubber.add_client_error('list_objects', service_error_code=code)
        yield stubber


def handle(event):
    response = api.list_urls(event, context={})
    return response['statusCode'], json.loads(response['body'])


class TestGetUrls:
    def test_valid_ok_response(self):
        with non_empty_bucket():
            event = request_by_user('user1')

            response = api.list_urls(event, context={})

            assert 'statusCode' in response and 'body' in response
            assert valid_json(response['body'])
            assert 'urls' in json.loads(response['body'])

    def test_valid_fail_response(self):
        with s3_read_error(500):
            event = request_by_user('user1')

            response = api.list_urls(event, context={})

            assert 'statusCode' in response and 'body' in response
            assert response['statusCode'] == 500
            assert valid_json(response['body'])
            assert 'message' in json.loads(response['body'])
            assert 'detail' in json.loads(response['body'])

    def test_only_urls_by_user1_are_reported(self):
        with non_empty_bucket():
            event = request_by_user('user1')

            status, body = handle(event)

            assert status == 200
            assert len(body['urls']) == 1
            assert body['urls'][0]['user'] == 'user1'
            assert body['urls'][0]['url'] == 'user1_link'

    def test_user_without_urls_gets_empty_list(self):
        with non_empty_bucket():
            event = request_by_user('user3')

            status, body = handle(event)

            assert status == 200
            assert not body['urls']
