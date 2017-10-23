import mock
from freezegun import freeze_time
import datetime
import pytest
from datetime import datetime, date, timedelta

from dmutils.email import EmailError
from dmscripts import notify_suppliers_about_withdrawn_briefs as tested_script


class TestMain:
    @mock.patch('dmscripts.notify_suppliers_about_withdrawn_briefs.dmapiclient.DataAPIClient')
    def test_main_calls_functions(self, data_api_client):
        with freeze_time('2016-01-29 03:04:05'):
            tested_script.main()
            yesterday = date(2016,1,28)
            expected_args = [mock.call('withdrawn_at', yesterday, yesterday, inclusive=True)]
            assert data_api_client.find_briefs_by_status_datestamp.call_args_list == expected_args
