from datetime import datetime

google = 'https://www.google.com'
bing = 'https://www.bing.com'


def assert_valid_date(s):
    try:
        datetime.fromisoformat(s)
        assert True
    except ValueError:
        assert False
