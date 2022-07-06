import api
import pytest
import re

from test_common import assert_valid_date, google
from test_contexts import anonymous_url_created_successfully, custom_url_created_successfully, path_already_taken


class TestShorten:
    def test_valid_url_ok(self):
        with anonymous_url_created_successfully(google):
            event = body(url=google)

            resp = call_shorten(event)

            assert type(resp) is dict
            assert resp['path'].isalnum()
            assert resp['links_to'] == google
            assert_valid_date(resp['created_at'])

    def test_domain_name_without_trailing_slash_ok(self):
        url = re.sub('/$', '', google)
        with anonymous_url_created_successfully(url):
            event = body(url=url)

            resp = call_shorten(event)

            assert resp['links_to'] == url

    def test_custom_path_ok(self):
        with custom_url_created_successfully(google, 'custom', 'user1'):
            event = body(url=google, custom_path='custom', user='user1')

            resp = call_shorten(event)

            assert resp['path'] == 'custom'

    def test_invalid_url_is_rejected(self):
        with pytest.raises(Exception, match=r'(?i)url.*invalid'):
            event = body(url='invalid url')
            call_shorten(event)

    def test_partial_url_is_rejected(self):
        with pytest.raises(Exception, match=r'(?i)url.*invalid'):
            url_without_schema = re.sub('^https://', '', google)
            event = body(url=url_without_schema)
            call_shorten(event)

    def test_invalid_path_is_rejected(self):
        with pytest.raises(Exception, match=r'(?i)path.*not.*match'):
            event = body(url=google, custom_path='no spaces allowed', user='user1')
            call_shorten(event)

    def test_custom_path_already_in_use_is_rejected(self):
        with path_already_taken('taken'), pytest.raises(Exception, match=r'(?i)path.*taken'):
            event = body(url=google, custom_path='taken', user='user1')
            call_shorten(event)


def body(**kwargs):
    data = dict(**kwargs)
    if 'user' in data:
        user = data.pop('user')
        return {'data': data, 'user': user}
    else:
        return {'data': data}


def call_shorten(event):
    return api.shorten_url(event, context={})
