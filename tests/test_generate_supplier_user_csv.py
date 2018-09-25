import builtins
import mock
import pytest

from dmscripts.generate_supplier_user_csv import (
    generate_csv_and_upload_to_s3, generate_supplier_csv, generate_user_csv, upload_to_s3
)


def test_generate_supplier_csv_calls_api_and_returns_csv():
    data_api_client = mock.Mock()
    data_api_client.export_suppliers.return_value = {
        'suppliers': [
            {
                'supplier_id': 1,
                'application_result': 'no result',
                'application_status': 'no_application',
                'declaration_status': 'unstarted',
                'framework_agreement': False,
                'supplier_name': "Supplier 1",
                'supplier_organisation_size': "small",
                'duns_number': "100000001",
                'registered_name': 'Registered Supplier Name 1',
                'companies_house_number': None,
                "published_services_count": {
                    "cloud-hosting": 2
                },
                "contact_information": {
                    'contact_name': 'Contact for Supplier 1',
                    'contact_email': 'hello@example.com',
                    'contact_phone_number': None,
                    'address_first_line': '7 Gem Lane',
                    'address_city': 'Cantelot',
                    'address_postcode': 'SW1A 1AA',
                    'address_country': 'country:GB',
                },
                'variations_agreed': '',
            }
        ]
    }
    data_api_client.get_framework.return_value = {
        'frameworks': {
            'lots': [
                {"id": 1, "slug": "cloud-hosting"},
            ]
        }
    }
    logger = mock.Mock()

    headers, rows, filename = generate_supplier_csv('g-cloud-10', data_api_client, logger)

    assert filename == 'official-details-for-suppliers-g-cloud-10'
    assert headers == [
        "supplier_id",
        "supplier_name",
        "supplier_organisation_size",
        "duns_number",
        "companies_house_number",
        "registered_name",
        "declaration_status",
        "application_status",
        "application_result",
        "framework_agreement",
        "variations_agreed",
        "total_number_of_services",
        'service-count-cloud-hosting',
        'contact_name',
        'contact_email',
        'contact_phone_number',
        'address_first_line',
        'address_city',
        'address_postcode',
        'address_country'
    ]
    assert rows[0] == [
        1, 'Supplier 1', 'small', '100000001', None, 'Registered Supplier Name 1',
        'unstarted', 'no_application', 'no result', False, '', 2, 2,
        'Contact for Supplier 1', 'hello@example.com',
        None, '7 Gem Lane', 'Cantelot', 'SW1A 1AA', 'country:GB'
    ]

    assert data_api_client.get_framework.call_args_list == [mock.call('g-cloud-10')]
    assert data_api_client.export_suppliers.call_args_list == [mock.call('g-cloud-10')]


@pytest.mark.parametrize('user_research_opted_in, expected_filename', [
    (True, 'user-research-suppliers-on-g-cloud-10'),
    (False, 'all-email-accounts-for-suppliers-g-cloud-10')
])
def test_generate_user_csv_calls_api_and_returns_csv(user_research_opted_in, expected_filename):
    data_api_client = mock.Mock()
    logger = mock.Mock()

    data_api_client.export_users.return_value = {
        'users': [
            {
                "application_result": "pass",
                "application_status": "no_application",
                "declaration_status": "unstarted",
                "email address": "1234@example.com",
                "framework_agreement": True,
                "published_service_count": 4,
                "supplier_id": 1234,
                "user_name": "Test user 1",
                "user_research_opted_in": True,
                "variations_agreed": ""
            },
            {
                "application_result": "pass",
                "application_status": "no_application",
                "declaration_status": "unstarted",
                "email address": "5678@example.com",
                "framework_agreement": True,
                "published_service_count": 3,
                "supplier_id": 5678,
                "user_name": "Test user 2",
                "user_research_opted_in": False,
                "variations_agreed": ""
            }
        ]
    }
    headers, rows, filename = generate_user_csv('g-cloud-10', data_api_client, user_research_opted_in, logger)

    assert filename == expected_filename
    assert headers == [
        "email address",
        "user_name",
        "supplier_id",
        "declaration_status",
        "application_status",
        "application_result",
        "framework_agreement",
        "variations_agreed",
        "published_service_count"
    ]
    assert rows[0] == [
        '1234@example.com',
        'Test user 1',
        1234,
        'unstarted',
        'no_application',
        'pass',
        True,
        '',
        4
    ]
    if not user_research_opted_in:
        # Additional row included
        assert rows[1] == [
            '5678@example.com',
            'Test user 2',
            5678,
            'unstarted',
            'no_application',
            'pass',
            True,
            '',
            3
        ]

    assert data_api_client.export_users.call_args_list == [mock.call('g-cloud-10')]


@pytest.mark.parametrize('dry_run', [False, True])
def test_upload_to_s3_uploads_or_logs_for_dry_run(dry_run):
    bucket = mock.Mock()
    logger = mock.Mock()

    with mock.patch.object(builtins, 'open', mock.mock_open(read_data='some csv rows')):
        upload_to_s3(
            'data/suppliers-export.csv', 'g-cloud-10', 'supplier-users-g-cloud-10.csv', bucket, dry_run, logger
        )

    if dry_run:
        assert bucket.save.call_args_list == []
        assert logger.info.call_args_list == [
            mock.call(
                "[Dry-run] UPLOAD: 'data/suppliers-export.csv' to 'supplier-users-g-cloud-10.csv'"
            )
        ]
    else:
        assert bucket.save.call_args_list == [
            mock.call(
                "g-cloud-10/reports/supplier-users-g-cloud-10.csv",
                mock.ANY,  # file object
                acl='private',
                download_filename='supplier-users-g-cloud-10.csv'
            )
        ]
        assert logger.info.call_args_list == [
            mock.call(
                "UPLOADED: 'data/suppliers-export.csv' to 'supplier-users-g-cloud-10.csv'"
            )
        ]


@mock.patch('dmscripts.generate_supplier_user_csv._build_csv')
@mock.patch('dmscripts.generate_supplier_user_csv.generate_supplier_csv')
@mock.patch('dmscripts.generate_supplier_user_csv.upload_to_s3')
def test_generate_supplier_csv_generates_csv_and_uploads_to_s3(upload_to_s3, generate_supplier_csv, build_csv):
    bucket, data_api_client = mock.Mock(), mock.Mock()
    generate_supplier_csv.return_value = ['header1', 'header2'], ['row1', 'row2'], 'filename'

    generate_csv_and_upload_to_s3(
        bucket, 'g-cloud-10', 'suppliers', 'data', data_api_client, logger='logger'
    )

    assert generate_supplier_csv.call_args_list == [
        mock.call('g-cloud-10', data_api_client, logger='logger')
    ]
    assert upload_to_s3.call_args_list == [
        mock.call(
            'data/filename.csv', 'g-cloud-10', 'filename.csv', bucket, dry_run=False, logger='logger'
        )
    ]


@mock.patch('dmscripts.generate_supplier_user_csv._build_csv')
@mock.patch('dmscripts.generate_supplier_user_csv.generate_user_csv')
@mock.patch('dmscripts.generate_supplier_user_csv.upload_to_s3')
def test_generate_user_csv_generates_csv_and_uploads_to_s3(upload_to_s3, generate_user_csv, build_csv):
    bucket, data_api_client = mock.Mock(), mock.Mock()
    generate_user_csv.return_value = ['header1', 'header2'], ['row1', 'row2'], 'filename'

    generate_csv_and_upload_to_s3(
        bucket, 'g-cloud-10', 'users', 'data', data_api_client, logger='logger'
    )

    assert generate_user_csv.call_args_list == [
        mock.call('g-cloud-10', data_api_client, user_research_opted_in=False, logger='logger')
    ]
    assert upload_to_s3.call_args_list == [
        mock.call(
            'data/filename.csv', 'g-cloud-10', 'filename.csv', bucket, dry_run=False, logger='logger'
        )
    ]
