import mock
import datetime

from dmscripts.helpers import brief_data_helpers


class TestGetClosedBriefs:

    def test_get_closed_briefs_filters_by_date_closed(self):
        api_client = mock.Mock()
        api_client.find_briefs_iter.return_value = iter([
            {"applicationsClosedAt": "2016-09-03T23:59:59.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-04T23:59:59.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-05T23:59:59.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-06T23:59:59.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-07T23:59:59.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-08T23:59:59.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-05T23:59:59.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-09T23:59:59.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-05T23:59:59.000000Z", "status": "closed"},
        ])

        assert brief_data_helpers.get_closed_briefs(
            api_client, datetime.date(2016, 9, 5)
        ) == [
            {"applicationsClosedAt": "2016-09-05T23:59:59.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-05T23:59:59.000000Z", "status": "closed"},
            {"applicationsClosedAt": "2016-09-05T23:59:59.000000Z", "status": "closed"},
        ]
