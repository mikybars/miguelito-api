import api

from operator import itemgetter
from test_common import google
from test_contexts import no_links_found_for_user, link_found_for_user


class TestList:
    def test_only_links_by_user1_are_returned(self):
        with link_found_for_user(user='user1', backhalf='0jY7IuW', origin=google):
            event = body(user='user1')

            resp = call_list(event)

            assert type(resp) is dict
            assert 'data' in resp
            data = resp['data']
            assert type(data) is list
            assert len(data) == 1
            assert itemgetter('user', 'backhalf', 'origin')(data[0]) == ('user1', '0jY7IuW', google)

    def test_user_without_links_gets_empty_list(self):
        with no_links_found_for_user('user1'):
            event = body(user='user1')

            resp = call_list(event)

            assert len(resp['data']) == 0


def body(**kwargs):
    return dict(**kwargs)


def call_list(event):
    return api.list_links(event, context={})
