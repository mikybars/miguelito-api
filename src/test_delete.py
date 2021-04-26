import api
import json
from test_contexts import url_owned_by_user, url_not_found, aws_s3_head_error


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


def handle(event):
    response = api.delete_url(event, context={})
    return response['statusCode']


class TestDelete:
    def test_url_owned_by_user_ok(self):
        with url_owned_by_user('user1'):
            event = request_by_user('user1', 'path1')
        
            status = handle(event)

            assert status == 200

    def test_url_not_owned_by_user_returns_forbidden(self):
        with url_owned_by_user('user1'):
            event = request_by_user('user2', 'path1')

            status = handle(event)

            assert status == 403

    def test_url_not_found_returns_forbidden(self):
        with url_not_found():
            event = request_by_user('user1', 'path1')

            status = handle(event)

            assert status == 403

    def test_aws_error_gets_reported(self):
        with aws_s3_head_error(403):
            event = request_by_user('user1', 'path1')

            status = handle(event)

            assert status == 500
