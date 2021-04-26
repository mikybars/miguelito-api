import api
import json
from test_contexts import url_already_existing, url_created_successfully, aws_s3_put_error


def body(url, custom_path=''):
    return {
        'body': json.dumps({
            'url': url,
            'custom_path': custom_path
        })
    }


def assert_bad_request(status, body):
    assert status == 400
    assert 'message' in body
    assert 'path' not in body


def handle(event):
    response = api.shorten_url(event, context={})
    return response['statusCode'], json.loads(response['body'])


class TestShorten:
    def test_valid_url_ok(self):
        with url_created_successfully():
            event = body('https://www.google.com')

            status, resp = handle(event)

            assert status == 200
            assert 'path' in resp and 'links_to' in resp
            assert resp['path'].isalnum()
            assert resp['links_to'] == 'https://www.google.com'

    def test_domain_name_without_trailing_slash_ok(self):
        with url_created_successfully():
            event = body('https://www.google.com')

            status, resp = handle(event)

            assert status == 200
            assert resp['links_to'] == 'https://www.google.com'

    def test_custom_path_ok(self):
        with url_created_successfully():
            event = body('https://www.google.com/', 'custom')

            status, resp = handle(event)

            assert status == 200
            assert resp['path'] == 'custom'

    def test_blank_custom_path_gets_a_random_url(self):
        with url_created_successfully():
            event = body('https://www.google.com/', '  ')

            status, resp = handle(event)

            assert status == 200
            assert resp['path'].isalnum()

    def test_invalid_url_is_rejected(self):
        event = body('invalid url')

        status, resp = handle(event)

        assert_bad_request(status, resp)

    def test_invalid_path_is_rejected(self):
        event = body('https://www.google.com', 'no spaces allowed')

        status, resp = handle(event)

        assert_bad_request(status, resp)

    def test_partial_url_is_rejected(self):
        event = body('www.google.com')

        status, resp = handle(event)

        assert_bad_request(status, resp)

    def test_custom_path_already_in_use_is_rejected(self):
        with url_already_existing():
            event = body('https://www.google.com/', 'custom')

            status, resp = handle(event)

            assert_bad_request(status, resp)

    def test_aws_error_gets_reported(self):
        with aws_s3_put_error(403):
            event = body('https://www.google.com/')

            status, resp = handle(event)

            assert status == 500
