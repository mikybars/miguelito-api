import pytest
import api

from operator import itemgetter
from test_common import assert_valid_date, bing, google
from test_contexts import duplicate_path_edit_error, edit_ok, path_not_found, path_owned_by_user


class TestEdit:
    def test_edit_successful_returns_updated_url(self):
        with edit_ok(user='user1', path='path1', origin=google, new_path='new-path', new_origin=bing):
            data = {
                'path': 'new-path',
                'origin': bing
            }
            event = body(path='path1', user='user1', data=data)

            resp = call_edit(event)

            assert type(resp) is dict
            assert itemgetter('path', 'links_to', 'user')(resp) == ('new-path', bing, 'user1')
            assert_valid_date(resp['updated_at'])
            assert resp['updated_at'] != resp['created_at']

    def test_path_not_found_returns_forbidden(self):
        with path_not_found('path1'), pytest.raises(Exception, match='forbidden'):
            event = body(path='path1', user='user1', data={'origin': google})
            call_edit(event)

    def test_url_not_owned_by_user_returns_forbidden(self):
        with path_owned_by_user('path1', google, 'user1'), pytest.raises(Exception, match='forbidden'):
            event = body(path='path1', user='otheruser', data={'origin': google})
            call_edit(event)

    def test_duplicate_path_raises_exception(self):
        with duplicate_path_edit_error('path1', google, 'user1', 'new-path'), pytest.raises(Exception,
                match=r'(?i).*path.*taken'):
            event = body(path='path1', user='user1', data={'path': 'new-path'})
            call_edit(event)


def body(**kwargs):
    return dict(**kwargs)


def call_edit(event):
    return api.edit_url(event, context={})
