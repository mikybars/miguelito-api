import boto3
from botocore.stub import Stubber
import json
from api import handle, s3_client


class TestApi:
    def test_valid_url(self):
        with Stubber(s3_client) as stubber:
            stubber.add_client_error('head_object', service_error_code='404')
            stubber.add_response('put_object', {})
            event = {
                'body': '{"url":"https://www.google.com/"}'
            }
            r = handle(event, context={})
            assert r['statusCode'] == 200
            TestApi.assert_body_contains(r, 'message', 'success')

    def test_partial_url(self):
        event = {
            'body': '{"url":"www.google.com"}'
        }
        r = handle(event, context={})
        assert r['statusCode'] == 400
        TestApi.assert_body_contains(r, 'message', 'invalid')

    def test_missing_url(self):
        event = {
            'body': '{}'
        }
        r = handle(event, context={})
        assert r['statusCode'] == 400
        TestApi.assert_body_contains(r, 'message', 'required')

    def test_blank_url(self):
        event = {
            'body': '{"url":"  "}'
        }
        r = handle(event, context={})
        assert r['statusCode'] == 400
        TestApi.assert_body_contains(r, 'message', 'required')

    @staticmethod
    def assert_body_contains(response, key, match):
        assert 'body' in response
        body = json.loads(response['body'])
        assert key in body
        assert match in body[key]
