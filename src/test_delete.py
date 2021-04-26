import api
import pytest
from test_contexts import url_owned_by_user, url_not_found


def body(**kwargs):
    return dict(**kwargs)


def handle(event):
    api.delete_url(event, context={})


class TestDelete:
    def test_url_owned_by_user_ok(self):
        with url_owned_by_user('user1'):
            event = body(path='path1', user='user1')
            handle(event)

    def test_url_not_owned_by_user_returns_forbidden(self):
        with url_owned_by_user('user1'), pytest.raises(Exception) as excinfo:
            event = body(path='path1', user='user2')
            handle(event)

        assert 'forbidden' == str(excinfo.value)

    def test_url_not_found_returns_forbidden(self):
        with url_not_found(), pytest.raises(Exception) as excinfo:
            event = body(path='path1', user='user1')
            handle(event)

        assert 'forbidden' == str(excinfo.value)
