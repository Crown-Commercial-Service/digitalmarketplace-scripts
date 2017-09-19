import datetime
import pytest
from freezegun import freeze_time

import dmscripts.helpers.date_helpers as date_helpers


@pytest.mark.parametrize(
    'datestring, expected_format', [(None, datetime.date(2015, 1, 1)), ('2016-01-02', datetime.date(2016, 1, 2))]
)
def test_get_date_closed(datestring, expected_format):

    with freeze_time('2015-01-02 03:04:05'):
        assert date_helpers.get_date_closed(datestring) == expected_format
