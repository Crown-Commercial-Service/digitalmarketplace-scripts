import mock
import datetime
import pytest

from dmscripts.helpers import brief_data_helpers


class TestGetBriefsClosedOnDate:

    def test_get_briefs_closed_on_date_filters_by_date_closed(self):
        api_client = mock.Mock()
        api_client.find_briefs_iter.return_value = iter([
            {"applicationsClosedAt": "2016-09-04T23:59:59.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-05T00:00:00.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-05T08:29:39.000001Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-05T23:59:59.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-06T00:00:00.000000Z", "status": "closed"},
        ])

        assert brief_data_helpers.get_briefs_closed_on_date(api_client, datetime.date(2016, 9, 5)) == [
            {"applicationsClosedAt": "2016-09-05T00:00:00.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-05T08:29:39.000001Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-05T23:59:59.000000Z", "status": "closed"},
        ]

    def test_get_briefs_closed_on_date_throws_error_for_briefs_without_application_closed_at(self):
        api_client = mock.Mock()
        api_client.find_briefs_iter.return_value = iter([
            {"applicationsClosedAt": "2016-09-05T23:59:59.000000Z", "status": "closed"},
            {"status": "closed"}
        ])

        with pytest.raises(KeyError):
            brief_data_helpers.get_briefs_closed_on_date(api_client, datetime.date(2016, 9, 5))
