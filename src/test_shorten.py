import pytest

import api
from test_contexts import path_already_taken, url_created_successfully


def body(**kwargs):
    return dict(**kwargs)


def handle(event):
    return api.shorten_url(event, context={})


class TestShorten:
    def test_valid_url_ok(self):
        with url_created_successfully():
            event = body(url='https://www.google.com')

            resp = handle(event)

            assert resp.path.isalnum()
            assert resp.links_to == 'https://www.google.com'

    def test_domain_name_without_trailing_slash_ok(self):
        with url_created_successfully():
            event = body(url='https://www.google.com')

            resp = handle(event)

            assert resp.links_to == 'https://www.google.com'

    def test_custom_path_ok(self):
        with url_created_successfully(with_user=True):
            event = body(url='https://www.google.com/', custom_path='custom', user='user1')

            resp = handle(event)

            assert resp.path == 'custom'

    def test_blank_custom_path_gets_a_random_url(self):
        with url_created_successfully(with_user=True):
            event = body(url='https://www.google.com/', custom_path='  ', user='user1')

            resp = handle(event)

            assert resp.path.isalnum()

    def test_invalid_url_is_rejected(self):
        with pytest.raises(Exception) as excinfo:
            event = body(url='invalid url')
            handle(event)
        assert 'URL' in str(excinfo.value)

    def test_invalid_path_is_rejected(self):
        with pytest.raises(Exception) as excinfo:
            event = body(url='https://www.google.com', custom_path='no spaces allowed', user='user1')
            handle(event)
        assert 'Path' in str(excinfo.value)

    def test_partial_url_is_rejected(self):
        with pytest.raises(Exception) as excinfo:
            event = body(url='www.google.com')
            handle(event)
        assert 'URL' in str(excinfo.value)

    def test_custom_path_already_in_use_is_rejected(self):
        with path_already_taken('taken'), pytest.raises(Exception) as excinfo:
            event = body(url='https://www.google.com/', custom_path='taken', user='user1')
            handle(event)
        assert 'Path' in str(excinfo.value)
