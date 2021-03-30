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


def handle(event):
    response = api.handle(event, context={})
    return response['statusCode'], json.loads(response['body'])


class TestApi:
    def test_valid_url(self):
        with link_does_not_exist_in_s3():
            event = {
                'body': '{"url":"https://www.google.com/"}'
            }

            status, body = handle(event)

            assert status == 200
            assert body['message'] == 'success'

    def test_partial_url(self):
        event = {
            'body': '{"url":"www.google.com"}'
        }

        status, body = handle(event)

        assert status == 400
        assert 'invalid' in body['message']
        assert 'path' not in body['message']

    def test_missing_url(self):
        event = {
            'body': '{}'
        }

        status, body = handle(event)

        assert status == 400
        assert 'required' in body['message']
        assert 'path' not in body['message']

    def test_blank_url(self):
        event = {
            'body': '{"url":"  "}'
        }

        status, body = handle(event)

        assert status == 400
        assert 'required' in body['message']
        assert 'path' not in body['message']

    def test_valid_custom_path(self):
        with link_does_not_exist_in_s3():
            event = {
                'body': '{"url":"https://www.google.com/", "custom_path": "custom"}'
            }

            status, body = handle(event)

            assert status == 200
            assert body['path'] == 'custom'

    def test_blank_custom_path(self):
        with link_does_not_exist_in_s3():
            event = {
                'body': '{"url":"https://www.google.com/", "custom_path": "  "}'
            }

            status, body = handle(event)

            assert status == 200
            assert len(body['path'].strip()) > 0

    def test_custom_path_already_in_use(self):
        with link_exists_in_s3():
            event = {
                'body': '{"url":"https://www.google.com/", "custom_path": "custom"}'
            }

            status, body = handle(event)

            assert status == 400
            assert 'already in use' in body['message']
            assert 'path' not in body
