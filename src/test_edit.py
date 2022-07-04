import pytest

import api
from test_contexts import edit_path_not_found


def body(**kwargs):
    return dict(**kwargs)


def handle(event):
    api.edit_url(event, context={})


class TestEdit:
    def test_url_not_owned_by_user_returns_forbidden(self):
        with edit_path_not_found('path1', 'user1'), pytest.raises(Exception) as excinfo:
            event = body(path='path1', user='user1', data={'path': 'new_path'})
            handle(event)

        assert 'forbidden' == str(excinfo.value)
