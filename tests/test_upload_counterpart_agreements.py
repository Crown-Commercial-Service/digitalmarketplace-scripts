import mock
import pytest
from sys import version_info
from freezegun import freeze_time
from dmscripts.upload_counterpart_agreements import upload_counterpart_file

if version_info.major == 2:
    import __builtin__ as builtins
else:
    import builtins


@pytest.mark.parametrize("notify_fail_early", (False, True,))  # should make no difference
@mock.patch('dmscripts.upload_counterpart_agreements.getpass.getuser')
def test_upload_counterpart_file_uploads_and_calls_api_if_not_dry_run(getuser, notify_fail_early):
    getuser.return_value = 'test user'
    bucket = mock.Mock()
    data_api_client = mock.Mock()
    data_api_client.get_supplier_framework_info.return_value = {
        "frameworkInterest": {
            "agreementId": 23,
            "declaration": {
                "nameOfOrganisation": "The supplier who signed",
            },
        }
    }

    with freeze_time('2016-11-12 13:14:15'):
        with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
            upload_counterpart_file(
                bucket,
                {
                    "name": "Gee Cloud Eight",
                    "slug": "g-cloud-8",
                },
                'pdfs/123456-file.pdf',
                False,
                data_api_client,
                notify_fail_early=notify_fail_early,
            )

            bucket.save.assert_called_once_with(
                "g-cloud-8/agreements/123456/123456-agreement-countersignature-2016-11-12-131415.pdf",
                mock.ANY,
                acl='private',
                move_prefix=None,
                download_filename='The_supplier_who_signed-123456-agreement-countersignature.pdf'
            )

            data_api_client.update_framework_agreement.assert_called_once_with(
                23,
                {
                    'countersignedAgreementPath':
                    'g-cloud-8/agreements/123456/123456-agreement-countersignature-2016-11-12-131415.pdf'
                },
                'upload-counterpart-agreements script run by test user'
            )


@pytest.mark.parametrize("notify_fail_early", (False, True,))  # should make no difference
def test_upload_counterpart_file_does_not_perform_actions_if_dry_run(notify_fail_early):
    bucket = mock.Mock()
    data_api_client = mock.Mock()
    data_api_client.get_supplier_framework_info.return_value = {
        "frameworkInterest": {
            "agreementId": 23,
            "declaration": {
                "nameOfOrganisation": "The supplier who signed",
                "primaryContactEmail": "supplier.primary@example.com",
            },
        },
    }
    data_api_client.find_users_iter.side_effect = lambda *args, **kwargs: iter((
        {
            "id": 111322,
            "emailAddress": "user.111322@example.com",
            "supplierId": 123456,
            "active": True,
        },
        {
            "id": 111321,
            "emailAddress": "user.111321@example.com",
            "supplierId": 123456,
            "active": True,
        },
    ))
    dm_notify_client = mock.Mock()
    dm_notify_client.send_email.side_effect = AssertionError("This shouldn't be called")

    with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
        upload_counterpart_file(
            bucket,
            {
                "name": "Dos Two",
                "slug": "digital-outcomes-and-specialists-2",
            },
            'pdfs/123456-file.pdf',
            True,
            data_api_client,
            dm_notify_client=dm_notify_client,
            notify_template_id="dead-beef-baad-f00d",
            notify_fail_early=notify_fail_early,
        )

        assert bucket.save.called is False
        assert data_api_client.update_framework_agreement.called is False
        data_api_client.find_users_iter.assert_called_with(supplier_id=123456)


@pytest.mark.parametrize("find_users_iterable,expected_send_email_emails", (
    (
        (
            {
                "id": 111322,
                "emailAddress": "user.111322@example.com",
                "supplierId": 123456,
                "active": True,
            },
            {
                "id": 111321,
                "emailAddress": "user.111321@example.com",
                "supplierId": 123456,
                "active": True,
            },
            {
                "id": 111320,
                "emailAddress": "user.111320@example.com",
                "supplierId": 123456,
                "active": False,
            },
            {
                "id": 111323,
                "emailAddress": "supplier.primary@example.com",
                "supplierId": 123456,
                "active": True,
            },
        ),
        (
            "supplier.primary@example.com",
            "user.111321@example.com",
            "user.111322@example.com",
        ),
    ),
    (
        (
            {
                "id": 111329,
                "emailAddress": "user.111329@example.com",
                "supplierId": 123456,
                "active": True,
            },
            {
                "id": 111320,
                "emailAddress": "user.111320@example.com",
                "supplierId": 123456,
                "active": False,
            },
        ),
        (
            "supplier.primary@example.com",
            "user.111329@example.com",
        ),
    ),
    (
        (
            {
                "id": 222765,
                "emailAddress": "user.222765@example.com",
                "supplierId": 123456,
                "active": False,
            },
        ),
        (
            "supplier.primary@example.com",
        ),
    ),
))
@pytest.mark.parametrize("notify_fail_early", (False, True,))  # should make no difference
def test_upload_counterpart_file_sends_correct_emails(
        notify_fail_early,
        find_users_iterable,
        expected_send_email_emails,
        ):
    bucket = mock.Mock()
    data_api_client = mock.Mock()
    data_api_client.get_supplier_framework_info.return_value = {
        "frameworkInterest": {
            "agreementId": 23,
            "declaration": {
                "nameOfOrganisation": "The supplier who signed",
                "primaryContactEmail": "supplier.primary@example.com",
            },
        },
    }
    data_api_client.find_users_iter.side_effect = lambda *args, **kwargs: iter(find_users_iterable)
    dm_notify_client = mock.Mock()

    with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
        upload_counterpart_file(
            bucket,
            {
                "name": "Dos Two",
                "slug": "digital-outcomes-and-specialists-2",
            },
            'pdfs/123456-file.pdf',
            False,
            data_api_client,
            dm_notify_client=dm_notify_client,
            notify_template_id="dead-beef-baad-f00d",
            notify_fail_early=notify_fail_early,
        )

        assert bucket.save.called is True
        assert data_api_client.update_framework_agreement.called is True
        data_api_client.find_users_iter.assert_called_with(supplier_id=123456)

        expected_personalisation = {
            "framework_slug": "digital-outcomes-and-specialists-2",
            "framework_name": "Dos Two",
            "supplier_name": "The supplier who signed",
        }

        assert sorted(dm_notify_client.send_email.call_args_list) == sorted(
            (
                (email, "dead-beef-baad-f00d", expected_personalisation),
                {"allow_resend": True},
            ) for email in expected_send_email_emails
        )
