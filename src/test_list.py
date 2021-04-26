import api
import json
from test_contexts import non_empty_bucket, aws_s3_list_error


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


def handle(event):
    response = api.list_urls(event, context={})
    return response['statusCode'], json.loads(response['body'])


class TestGetUrls:
    def test_only_urls_by_user1_are_reported(self):
        with non_empty_bucket():
            event = request_by_user('user1')

            status, body = handle(event)

            assert status == 200
            assert 'urls' in body
            assert len(body['urls']) == 1
            assert body['urls'][0]['owner'] == 'user1'
            assert body['urls'][0]['links_to'] == 'user1_link'

    def test_user_without_urls_gets_empty_list(self):
        with non_empty_bucket():
            event = request_by_user('user3')

            status, body = handle(event)

            assert status == 200
            assert len(body['urls']) == 0

    def test_aws_error_gets_reported(self):
        with aws_s3_list_error(403):
            event = request_by_user('user1')

            status, resp = handle(event)

            assert status == 500
