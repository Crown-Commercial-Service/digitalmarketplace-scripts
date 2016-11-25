import mock
from sys import version_info
from freezegun import freeze_time
from dmscripts.upload_counterpart_agreements import upload_counterpart_file

if version_info.major == 2:
    import __builtin__ as builtins
else:
    import builtins


@mock.patch('dmscripts.upload_counterpart_agreements.getpass.getuser')
def test_upload_counterpart_file_uploads_and_calls_api_if_not_dry_run(getuser):
    getuser.return_value = 'test user'
    bucket = mock.Mock()
    client = mock.Mock()
    logger = mock.Mock()
    client.get_supplier_framework_info.return_value = {
        "frameworkInterest": {
            "agreementId": 23,
            "declaration": {"nameOfOrganisation": "The supplier who signed"}
        }
    }

    with freeze_time('2016-11-12 13:14:15'):
        with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
            upload_counterpart_file(bucket, 'g-cloud-8', 'pdfs/123456-file.pdf', False, client, logger)

            bucket.save.assert_called_once_with(
                "g-cloud-8/agreements/123456/123456-agreement-countersignature-2016-11-12-131415.pdf",
                mock.ANY,
                acl='private',
                move_prefix=None,
                download_filename='The_supplier_who_signed-123456-agreement-countersignature.pdf'
            )

            client.update_framework_agreement.assert_called_once_with(
                23,
                {'countersignedAgreementPath':
                    'g-cloud-8/agreements/123456/123456-agreement-countersignature-2016-11-12-131415.pdf'
                 },
                'upload-counterpart-agreements script run by test user'
            )


def test_upload_counterpart_file_does_not_upload_or_call_api_if_dry_run():
    bucket = mock.Mock()
    client = mock.Mock()
    logger = mock.Mock()
    client.get_supplier_framework_info.return_value = {
        "frameworkInterest": {
            "agreementId": 23,
            "declaration": {"nameOfOrganisation": "The supplier who signed"}
        }
    }

    with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
        upload_counterpart_file(bucket, 'g-cloud-8', 'pdfs/123456-file.pdf', True, client, logger)

        bucket.save.assert_not_called()
        client.update_framework_agreement.assert_not_called()
