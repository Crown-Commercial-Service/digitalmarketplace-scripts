import builtins
import mock
import pytest
from dmapiclient import DataAPIClient
from dmtestutils.api_model_stubs import BriefResponseStub, FrameworkStub

from dmscripts.export_dos_opportunities import (
    get_brief_data,
    get_latest_dos_framework,
    upload_file_to_s3,
    format_datetime_string_as_date,
    remove_username_from_email_address
)


example_brief = {
    "id": 12345,
    "title": "My Brilliant Brief",
    "frameworkSlug": "digital-outcomes-and-specialists-3",
    "lotSlug": "digital-specialists",
    "specialist": "technicalArchitect",
    "organisation": "HM Dept of Doing Stuff",
    "location": "London",
    "publishedAt": "2019-01-01T00:00:00.123456Z",
    "contractLength": "6 months",
    "status": "awarded",
    "users": [
        {"emailAddress": "shouldnt-be-visible@example.gov.uk"}
    ]
}


# TODO: replace with BriefResponseStub once awardedContractStartDate format is fixed
example_winning_brief_response = {
    "briefId": 12345,
    "supplierName": "Foo Inc",
    "supplierOrganisationSize": "small",
    "status": "awarded",
    "awardDetails": {
        "awardedContractValue": "2345678",
        "awardedContractStartDate": "2019-06-02"
    }
}


class TestFormatDatetimeStringAsDate:

    def test_format_datetime_string_as_date(self):
        initial_date = "2016-10-08T12:00:00.00000Z"
        formatted_date = "2016-10-08"
        assert format_datetime_string_as_date(initial_date) == formatted_date

    def test_format_datetime_string_as_date_raises_error_if_initial_date_format_incorrect(self):
        initial_dates = (
            "2016-10-08T12:00:00.00000",
            "2016-10-08T12:00:00",
            "2016-10-08"
        )
        for date in initial_dates:
            with pytest.raises(ValueError) as excinfo:
                format_datetime_string_as_date(date)

            assert "time data '{}' does not match format".format(date) in str(excinfo.value)


class TestRemoveUsernameFromEmailAddress:

    def test_remove_username_from_email_address(self):
        initial_email_address = "user.name@domain.com"
        formatted_email_address = "domain.com"
        assert remove_username_from_email_address(initial_email_address) == formatted_email_address


class TestGetLatestDOSFramework:

    def test_get_latest_dos_framework(self):
        client = mock.Mock(spec=DataAPIClient)
        client.find_frameworks.return_value = {
            'frameworks': [
                FrameworkStub(status='expired', slug='g-cloud-10', family='g-cloud').response(),
                FrameworkStub(status='live', slug='g-cloud-11', family='g-cloud').response(),
                FrameworkStub(
                    status='expired',
                    slug='digital-outcomes-and-specialists-2',
                    family='digital-outcomes-and-specialists'
                ).response(),
                FrameworkStub(
                    status='live',
                    slug='digital-outcomes-and-specialists-3',
                    family='digital-outcomes-and-specialists'
                ).response(),
            ]
        }

        assert get_latest_dos_framework(client) == 'digital-outcomes-and-specialists-3'
        assert client.find_frameworks.call_args_list == [
            mock.call()
        ]


class TestGetBriefData:

    def test_get_brief_data(self):
        client = mock.Mock(spec=DataAPIClient)
        client.find_briefs_iter.return_value = [example_brief]
        client.find_brief_responses_iter.return_value = [
            example_winning_brief_response,
            BriefResponseStub().response()
        ]

        logger = mock.Mock()

        rows = get_brief_data(client, logger)

        assert rows == [
            [
                12345,
                'My Brilliant Brief',
                'https://www.digitalmarketplace.service.gov.uk/digital-outcomes-and-specialists/opportunities/12345',
                'digital-outcomes-and-specialists-3',
                'digital-specialists',
                'technicalArchitect',
                "HM Dept of Doing Stuff",
                "example.gov.uk",
                "London",
                "2019-01-01",
                "2 weeks",
                "6 months",
                2,
                0,
                2,
                "awarded",
                "Foo Inc",
                "small",
                "2345678",
                "2019-06-02"
            ]
        ]

        assert client.find_briefs_iter.call_args_list == [
            mock.call(status="closed,awarded,unsuccessful,cancelled", with_users=True)
        ]
        assert client.find_brief_responses_iter.call_args_list == [
            mock.call(brief_id=12345)
        ]
        assert logger.info.call_args_list == [
            mock.call('Fetching closed briefs from API'),
            mock.call('Fetching brief responses for Brief ID 12345')
        ]


class TestUploadFileToS3:

    @pytest.mark.parametrize('dry_run', ['True', 'False'])
    def test_upload_file_to_s3(self, dry_run):
        bucket = mock.Mock()
        bucket.bucket_name = 'mybucket'
        logger = mock.Mock()

        with mock.patch.object(builtins, 'open', mock.mock_open()) as mock_open:
            upload_file_to_s3(
                "local/path", bucket, "remote/key/name", "opportunity-data.csv", dry_run, logger
            )

        assert mock_open.called is True
        assert bucket.save.call_args_list == ([] if dry_run else [
            mock.call("remote/key/name", "local/path", acl='public-read', download_filename="opportunity-data.csv")
        ])
        assert logger.info.call_args_list == ([
            mock.call("[Dry-run]UPLOAD: local/path to mybucket::opportunity-data.csv")
        ] if dry_run else [
            mock.call("UPLOAD: local/path to mybucket::opportunity-data.csv")
        ])
