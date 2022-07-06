import api

from operator import itemgetter
from test_common import google
from test_contexts import no_urls_found_for_user, url_found_for_user


class TestList:
    def test_only_urls_by_user1_are_returned(self):
        with url_found_for_user('user1', path='0jY7IuW', links_to=google):
            event = body(user='user1')

            resp = call_list(event)

            assert type(resp) is dict
            assert 'urls' in resp
            data = resp['urls']
            assert type(data) is list
            assert len(data) == 1
            assert itemgetter('user', 'path', 'links_to')(data[0]) == ('user1', '0jY7IuW', google)

    def test_user_without_urls_gets_empty_list(self):
        with no_urls_found_for_user('user1'):
            event = body(user='user1')

            resp = call_list(event)

            assert len(resp['urls']) == 0


def body(**kwargs):
    return dict(**kwargs)


def call_list(event):
    return api.list_urls(event, context={})
