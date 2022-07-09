import api
import pytest
import re

from test_common import assert_valid_date, google
from test_contexts import anonymous_link_created_successfully, custom_link_created_successfully, backhalf_already_taken


class TestShorten:
    def test_valid_origin_ok(self):
        with anonymous_link_created_successfully(google):
            event = body(origin=google)

            resp = call_create(event)

            assert type(resp) is dict
            assert resp['backhalf'].isalnum()
            assert resp['origin'] == google
            assert_valid_date(resp['created_at'])

    def test_domain_name_without_trailing_slash_ok(self):
        url = re.sub('/$', '', google)
        with anonymous_link_created_successfully(url):
            event = body(origin=url)

            resp = call_create(event)

            assert resp['origin'] == url

    def test_custom_link_ok(self):
        with custom_link_created_successfully(google, 'custom', 'user1'):
            event = body(origin=google, backhalf='custom', user='user1')

            resp = call_create(event)

            assert resp['backhalf'] == 'custom'

    def test_invalid_url_is_rejected(self):
        with pytest.raises(Exception, match=r'(?i)url.*invalid'):
            event = body(origin='invalid url')
            call_create(event)

    def test_partial_url_is_rejected(self):
        with pytest.raises(Exception, match=r'(?i)url.*invalid'):
            url_without_schema = re.sub('^https://', '', google)
            event = body(origin=url_without_schema)
            call_create(event)

    def test_invalid_backhalf_is_rejected(self):
        with pytest.raises(Exception, match=r'(?i)backhalf.*not.*match'):
            event = body(origin=google, backhalf='no spaces allowed', user='user1')
            call_create(event)

    def test_backhalf_already_taken_is_rejected(self):
        with backhalf_already_taken('taken'), pytest.raises(Exception, match=r'(?i)backhalf.*taken'):
            event = body(origin=google, backhalf='taken', user='user1')
            call_create(event)


def body(**kwargs):
    data = dict(**kwargs)
    if 'user' in data:
        user = data.pop('user')
        return {'data': data, 'user': user}
    else:
        return {'data': data}


def call_create(event):
    return api.create_link(event, context={})
