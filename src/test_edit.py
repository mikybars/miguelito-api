import pytest
import api

from operator import itemgetter
from test_common import assert_valid_date, bing, google
from test_contexts import duplicate_backhalf_edit_error, edit_ok, link_not_found, link_owned_by_user


class TestEdit:
    def test_edit_successful_returns_updated_link(self):
        with edit_ok(user='user1', backhalf='path1', origin=google, new_backhalf='new-path', new_origin=bing):
            data = {
                'backhalf': 'new-path',
                'origin': bing
            }
            event = body(backhalf='path1', user='user1', data=data)

            resp = call_edit(event)

            assert type(resp) is dict
            assert itemgetter('backhalf', 'origin', 'user')(resp) == ('new-path', bing, 'user1')
            assert_valid_date(resp['updated_at'])
            assert resp['updated_at'] != resp['created_at']

    def test_link_not_found_returns_forbidden(self):
        with link_not_found('path1'), pytest.raises(Exception, match='forbidden'):
            event = body(backhalf='path1', user='user1', data={'origin': google})
            call_edit(event)

    def test_link_not_owned_by_user_returns_forbidden(self):
        with link_owned_by_user('path1', google, 'user1'), pytest.raises(Exception, match='forbidden'):
            event = body(backhalf='path1', user='otheruser', data={'origin': google})
            call_edit(event)

    def test_duplicate_backhalf_raises_exception(self):
        with duplicate_backhalf_edit_error('path1', google, 'user1', 'new-path'), pytest.raises(Exception,
                match=r'(?i).*backhalf.*taken'):
            event = body(backhalf='path1', user='user1', data={'backhalf': 'new-path'})
            call_edit(event)


def body(**kwargs):
    return dict(**kwargs)


def call_edit(event):
    return api.edit_link(event, context={})
