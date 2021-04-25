import api
import boto3, json
from api import s3_client as s3
from botocore.stub import Stubber
from contextlib import contextmanager


@contextmanager
def link_exists_in_s3():
    with Stubber(s3) as stubber:
        stubber.add_response('head_object', {})
        yield stubber


@contextmanager
def link_does_not_exist_in_s3():
    with Stubber(s3) as stubber:
        stubber.add_client_error('head_object', service_error_code='404')
        stubber.add_response('put_object', {})
        yield stubber


@contextmanager
def s3_write_error(code):
    with Stubber(s3) as stubber:
        stubber.add_client_error('head_object', service_error_code='404')
        stubber.add_client_error('put_object', service_error_code=str(code))
        yield stubber


def handle(event):
    response = api.shorten_url(event, context={})
    return response['statusCode'], json.loads(response['body'])


def valid_json(data):
    try:
        json.loads(data)
        return True
    except ValueError:
        return False


class TestShorten:
    def test_valid_ok_response(self):
        with link_does_not_exist_in_s3():
            event = {
                'body': '{"url":"https://www.google.com/"}'
            }

            response = api.shorten_url(event, context={})

            assert 'statusCode' in response and 'body' in response
            assert valid_json(response['body'])
            assert 'path' in json.loads(response['body'])

    def test_valid_fail_response(self):
        with link_does_not_exist_in_s3():
            event = {
                'body': '{}'
            }

            response = api.shorten_url(event, context={})

            assert 'statusCode' in response and 'body' in response
            assert valid_json(response['body'])
            assert 'message' in json.loads(response['body'])

    def test_valid_url_gets_shortened(self):
        with link_does_not_exist_in_s3():
            event = {
                'body': '{"url":"https://www.google.com/"}'
            }

            status, body = handle(event)

            assert status == 200
            assert body['path'].isalnum()

    def test_partial_url_is_rejected(self):
        event = {
            'body': '{"url":"www.google.com"}'
        }

        status, body = handle(event)

        assert status == 400
        assert 'invalid' in body['message']
        assert 'path' not in body['message']

    def test_domain_name_without_trailing_slash_gets_shortened(self):
        with link_does_not_exist_in_s3():
            event = {
                'body': '{"url":"https://www.google.com"}'
            }

            status, body = handle(event)

            assert status == 200
            assert body['path'].isalnum()

    def test_valid_custom_path(self):
        with link_does_not_exist_in_s3():
            event = {
                'body': '{"url":"https://www.google.com/", "custom_path": "custom"}'
            }

            status, body = handle(event)

            assert status == 200
            assert body['path'] == 'custom'

    def test_blank_custom_path_gets_a_random_url(self):
        with link_does_not_exist_in_s3():
            event = {
                'body': '{"url":"https://www.google.com/", "custom_path": "  "}'
            }

            status, body = handle(event)

            assert status == 200
            assert body['path'].isalnum()

    def test_custom_path_already_in_use_is_rejected(self):
        with link_exists_in_s3():
            event = {
                'body': '{"url":"https://www.google.com/", "custom_path": "custom"}'
            }

            status, body = handle(event)

            assert status == 400
            assert 'already in use' in body['message']
            assert 'path' not in body

    def test_s3_error_gets_reported(self):
        with s3_write_error(500):
            event = {
                'body': '{"url":"https://www.google.com/"}'
            }

            status, body = handle(event)

            assert status == 500
