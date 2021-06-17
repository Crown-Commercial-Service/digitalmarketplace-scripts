import builtins
import csv
from collections import OrderedDict
from pathlib import Path

import mock
import pytest

from dmapiclient import DataAPIClient
from dmtestutils.api_model_stubs import BriefResponseStub, FrameworkStub

from dmscripts.export_dos_opportunities import (
    get_brief_data,
    get_latest_dos_framework,
    upload_file_to_s3,
    format_datetime_string_as_date,
    remove_username_from_email_address,
    export_dos_opportunities,
)

example_brief = {
    "id": 12345,
    "title": "My Brilliant Brief",
    "frameworkSlug": "digital-outcomes-and-specialists-3",
    "lotSlug": "digital-specialists",
    "specialistRole": "technicalArchitect",
    "organisation": "HM Dept of Doing Stuff",
    "location": "London",
    "publishedAt": "2019-01-01T00:00:00.123456Z",
    "contractLength": "6 months",
    "employmentStatus": "Contracted out service: the off-payroll rules do not apply",
    "status": "awarded",
    "users": [
        {
            "name": "My Name",
            "emailAddress": "private-email-address@example.gov.uk",
            "phoneNumber": "07700 900461",
        }
    ],
    "clarificationQuestions": [
        {
            "answer": "sometimes.",
            "publishedAt": "2016-05-05T16:19:15.618981Z",
            "question": "Is the sky blue?"
        }
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

        for row in rows:
            assert isinstance(row, OrderedDict)

        assert rows == [
            OrderedDict((
                ("ID", 12345),
                ("Opportunity", "My Brilliant Brief"),
                (
                    "Link",
                    "https://www.digitalmarketplace.service.gov.uk/digital-outcomes-and-specialists/opportunities/12345"
                ),
                ("Framework", "digital-outcomes-and-specialists-3"),
                ("Category", "digital-specialists"),
                ("Specialist", "technicalArchitect"),
                ("Organisation Name", "HM Dept of Doing Stuff"),
                ("Buyer Domain", "example.gov.uk"),
                ("Location Of The Work", "London"),
                ("Published At", "2019-01-01"),
                ("Open For", "2 weeks"),
                ("Expected Contract Length", "6 months"),
                ("Applications from SMEs", 2),
                ("Applications from Large Organisations", 0),
                ("Total Organisations", 2),
                ("Status", "awarded"),
                ("Winning supplier", "Foo Inc"),
                ("Size of supplier", "small"),
                ("Contract amount", "2345678"),
                ("Contract start date", "2019-06-02"),
                ("Clarification questions", 1),
                ("Employment status", "Contracted out service: the off-payroll rules do not apply"),
            ))
        ]

        assert client.find_briefs_iter.call_args_list == [
            mock.call(status="closed,awarded,unsuccessful,cancelled", with_users=True,
                      with_clarification_questions=True)
        ]
        assert client.find_brief_responses_iter.call_args_list == [
            mock.call(brief_id=12345)
        ]
        assert logger.info.call_args_list == [
            mock.call('Fetching closed briefs from API'),
            mock.call('Fetching brief responses for Brief ID 12345')
        ]

    def test_get_brief_data_with_buyer_user_details(self):
        client = mock.Mock(spec=DataAPIClient)
        client.find_briefs_iter.return_value = [example_brief]
        client.find_brief_responses_iter.return_value = [
            example_winning_brief_response,
            BriefResponseStub().response()
        ]

        logger = mock.Mock()

        row = get_brief_data(client, logger, include_buyer_user_details=True)[0]

        assert list(row.keys())[-3:] == [
            "Buyer user name", "Buyer email address", "Buyer phone number"
        ]

        assert row["Buyer user name"] == "My Name"
        assert row["Buyer email address"] == "private-email-address@example.gov.uk"
        assert row["Buyer phone number"] == "07700 900461"


class TestUploadFileToS3:

    @pytest.mark.parametrize('dry_run', ['True', 'False'])
    def test_upload_file_to_s3(self, dry_run):
        bucket = mock.Mock()
        bucket.bucket_name = 'mybucket'
        logger = mock.Mock()

        with mock.patch.object(builtins, 'open', mock.mock_open()) as mock_open:
            upload_file_to_s3(
                "local/path",
                bucket,
                "remote/key/name",
                "opportunity-data.csv",
                dry_run=dry_run,
                logger=logger
            )

        assert mock_open.called is True
        assert bucket.save.call_args_list == ([] if dry_run else [
            mock.call("remote/key/name", "local/path", acl='public-read', download_filename="opportunity-data.csv")
        ])
        assert logger.info.call_args_list == ([
            mock.call(
                "[Dry-run]UPLOAD: local/path to s3://mybucket/remote/key/name with acl public-read"
            )
        ] if dry_run else [
            mock.call("UPLOAD: local/path to s3://mybucket/remote/key/name with acl public-read")
        ])


class TestExportDOSOpportunities:
    @pytest.fixture
    def data_api_client(self):
        data_api_client = mock.Mock(spec=DataAPIClient)

        data_api_client.find_frameworks.return_value = {
            "frameworks": [
                FrameworkStub(
                    status="live",
                    slug="digital-outcomes-and-specialists-3",
                    family="digital-outcomes-and-specialists"
                ).response(),
            ]
        }

        data_api_client.find_briefs_iter.return_value = [example_brief]
        data_api_client.find_brief_responses_iter.return_value = [
            example_winning_brief_response,
            BriefResponseStub().response()
        ]

        return data_api_client

    @pytest.fixture
    def logger(self):
        return mock.Mock()

    @pytest.fixture(autouse=True)
    def s3(self):
        with mock.patch("dmscripts.export_dos_opportunities.S3") as S3:
            yield S3

    def test_it_uploads_brief_data_to_s3_as_a_csv(
        self, data_api_client, logger, s3, tmp_path
    ):
        export_dos_opportunities(
            data_api_client,
            logger,
            stage="development",
            output_dir=tmp_path,
            dry_run=False,
        )

        assert (tmp_path / "opportunity-data.csv").exists()
        assert mock.call(
            "digital-outcomes-and-specialists-3/communications/data/opportunity-data.csv",
            mock.ANY,  # CSV file
            acl="public-read",
            download_filename="opportunity-data.csv",
        ) in s3().save.call_args_list
        assert Path(s3().save.call_args_list[1][0][1].name) \
            == (tmp_path / "opportunity-data.csv")

    def test_public_csv_does_not_contain_buyer_user_details(
        self, data_api_client, logger, s3, tmp_path
    ):
        export_dos_opportunities(
            data_api_client,
            logger,
            stage="development",
            output_dir=tmp_path,
            dry_run=False,
        )

        public_csv = (tmp_path / "opportunity-data.csv").read_text()
        assert "private-email-address@example.gov.uk" not in public_csv
        assert "My Name" not in public_csv
        assert "07700 900461" not in public_csv

        header_row = public_csv.splitlines()[0].lower()
        assert "user name" not in header_row
        assert "email address" not in header_row
        assert "phone number" not in header_row

    @pytest.mark.parametrize("dry_run", (True, False))
    def test_uploads_csv_with_buyer_user_details_to_reports_bucket(
        self, data_api_client, logger, dry_run, s3, tmp_path
    ):
        export_dos_opportunities(
            data_api_client,
            logger,
            stage="development",
            output_dir=tmp_path,
            dry_run=dry_run,
        )

        with open(tmp_path / "opportunity-data.csv", newline="") as f:
            public_csv = csv.reader(f)
            public_csv_rows = list(public_csv)

        with open(tmp_path / "opportunity-data-for-admins.csv", newline="") as f:
            admin_csv = csv.reader(f)
            admin_csv_rows = list(admin_csv)

        header_row = admin_csv_rows[0]
        assert header_row[:-3] == public_csv_rows[0]
        assert header_row[-3:] == [
            "Buyer user name", "Buyer email address", "Buyer phone number"
        ]

        assert admin_csv_rows[1][:-3] == public_csv_rows[1]
        assert admin_csv_rows[1][-3:] == [
            "My Name", "private-email-address@example.gov.uk", "07700 900461"
        ]

        if dry_run is False:
            assert mock.call(
                "digital-outcomes-and-specialists-3/reports/opportunity-data.csv",
                mock.ANY,  # CSV file
                acl="bucket-owner-full-control",
                download_filename="opportunity-data.csv",
            ) in s3().save.call_args_list
            assert Path(s3().save.call_args_list[0][0][1].name) \
                == (tmp_path / "opportunity-data-for-admins.csv")
        else:
            assert s3().save.called is False
