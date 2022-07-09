import pytest
import api

from test_contexts import delete_link_not_found


class TestDelete:
    def test_link_not_owned_by_user_returns_forbidden(self):
        with delete_link_not_found('path1', 'user1'), pytest.raises(Exception, match='forbidden'):
            event = body(backhalf='path1', user='user1')
            call_delete(event)


def body(**kwargs):
    return dict(**kwargs)


def call_delete(event):
    api.delete_link(event, context={})
