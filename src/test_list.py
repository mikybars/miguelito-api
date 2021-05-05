import api
from test_contexts import url_by_user, no_urls_by_user


def body(**kwargs):
    return dict(**kwargs)


def handle(event):
    return api.list_urls(event, context={})


class TestGetUrls:
    def test_only_urls_by_user1_are_reported(self):
        with url_by_user('user1', path='0jY7IuW', links_to='https://www.google.com'):
            event = body(user='user1')

            resp = handle(event)

            assert 'urls' in resp
            assert len(resp['urls']) == 1
            assert resp['urls'][0].user == 'user1'
            assert resp['urls'][0].path == '0jY7IuW'
            assert resp['urls'][0].links_to == 'https://www.google.com'

    def test_user_without_urls_gets_empty_list(self):
        with no_urls_by_user('user2'):
            event = body(user='user2')

            resp = handle(event)

            assert len(resp['urls']) == 0
