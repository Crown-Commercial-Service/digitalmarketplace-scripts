import datetime
from freezegun import freeze_time

import dmscripts.helpers.date_helpers as date_helpers


def test_get_date_closed():
    def check_date_closed(value, expected):
        with freeze_time('2015-01-02 03:04:05'):
            assert date_helpers.get_date_closed(value) == expected

    for value, expected in [
        (None, datetime.date(2015, 1, 1)),
        ('2016-01-02', datetime.date(2016, 1, 2))
    ]:
        yield check_date_closed, value, expected
