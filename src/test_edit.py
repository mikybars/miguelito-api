import pytest

import api
from test_contexts import edit_ok, path_not_found, path_owned_by_user, duplicate_path_edit_error


def body(**kwargs):
    return dict(**kwargs)


def handle(event):
    return api.edit_url(event, context={})


class TestEdit:
    def test_edit_successful_returns_updated_url(self):
        with edit_ok(user='user1', path='path1', origin='https://www.google.com',
                new_path='new-path', new_origin='https://www.bing.com'):
            data = {
                'path': 'new-path',
                'origin': 'https://www.bing.com'
            }
            event = body(path='path1', user='user1', data=data)

            resp = handle(event)

            assert type(resp) is dict
            assert resp['path'] == 'new-path'
            assert resp['links_to'] == 'https://www.bing.com'
            assert resp['user'] == 'user1'
            assert resp['updated_at'] != resp['created_at']

    def test_path_not_found_returns_forbidden(self):
        with path_not_found('path1'), pytest.raises(Exception, match='forbidden'):
            event = body(path='path1', user='user1', data={'origin': 'https://www.google.com'})
            handle(event)

    def test_url_not_owned_by_user_returns_forbidden(self):
        with path_owned_by_user('path1', 'user1'), pytest.raises(Exception, match='forbidden'):
            event = body(path='path1', user='otheruser', data={'origin': 'https://www.google.com'})
            handle(event)

    def test_duplicate_path_raises_exception(self):
        with duplicate_path_edit_error('path1', 'user1', 'new-path'), pytest.raises(Exception,
                match=r'(?i).*path.*taken'):
            event = body(path='path1', user='user1', data={'path': 'new-path'})
            handle(event)
