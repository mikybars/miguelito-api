import api
from test_contexts import non_empty_bucket


def body(**kwargs):
    return dict(**kwargs)


def handle(event):
    return api.list_urls(event, context={})


class TestGetUrls:
    def test_only_urls_by_user1_are_reported(self):
        with non_empty_bucket():
            event = body(user='user1')

            resp = handle(event)

            assert 'urls' in resp
            assert len(resp['urls']) == 1
            assert resp['urls'][0].user == 'user1'
            assert resp['urls'][0].links_to == 'user1_link'

    def test_user_without_urls_gets_empty_list(self):
        with non_empty_bucket():
            event = body(user='user3')

            resp = handle(event)

            assert len(resp['urls']) == 0
