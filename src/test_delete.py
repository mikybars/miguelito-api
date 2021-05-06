import api
import pytest
from test_contexts import delete_path_not_found


def body(**kwargs):
    return dict(**kwargs)


def handle(event):
    api.delete_url(event, context={})


class TestDelete:
    def test_url_not_owned_by_user_returns_forbidden(self):
        with delete_path_not_found(), pytest.raises(Exception) as excinfo:
            event = body(path='path1', user='user1')
            handle(event)

        assert 'forbidden' == str(excinfo.value)
