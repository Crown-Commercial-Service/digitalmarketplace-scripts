import mock
import pytest
import builtins
from freezegun import freeze_time
from dmapiclient import DataAPIClient
from scripts.oneoff.upload_draft_service_pdfs import (
    upload_to_submissions_bucket,
    get_info_from_filename,
    update_draft_service_with_document_paths,
    upload_draft_service_pdfs_from_folder
)


class TestUploadToSubmissionsBucket:

    @pytest.mark.parametrize('dry_run', (True, False))
    def test_upload_to_submissions_bucket_uploads_if_not_dry_run(self, dry_run):
        bucket = mock.Mock()
        with mock.patch.object(builtins, 'open', mock.mock_open()) as mock_open:
            upload_to_submissions_bucket(
                "pricing.pdf", bucket, "submissions", "g-cloud-12", 12345, "/path/to/file", dry_run, None
            )

        assert bucket.save.called is False if dry_run else bucket.save.called_once_with(
            "g-cloud-12/submissions/12345/pricing.pdf",
            mock_open,
            acl='bucket-owner-full-control',
            download_filename=None
        )

    def test_upload_to_submissions_bucket_uploads_with_supplier_download_name(self):
        bucket = mock.Mock()
        with mock.patch.object(builtins, 'open', mock.mock_open()) as mock_open:
            upload_to_submissions_bucket(
                "pricing.pdf", bucket, "submissions", "g-cloud-12", 12345, "/path/to/file", False,
                {12345: "ACME LTD"}
            )

        assert bucket.save.call_args_list == [
            mock.call(
                "g-cloud-12/submissions/12345/pricing.pdf",
                mock_open.return_value,
                acl='bucket-owner-full-control',
                download_filename="ACME_LTD-12345-pricing.pdf"
            )
        ]


class TestGetInfoFromFilename:

    @pytest.mark.parametrize(
        'matching_drafts, expected_result',
        [
            (555, 555),
            (None, None),
            ('multi', None)
        ]
    )
    @mock.patch('scripts.oneoff.upload_draft_service_pdfs.find_draft_id_by_service_name')
    def test_get_info_from_filename(self, find_draft_id_by_service_name, matching_drafts, expected_result):
        find_draft_id_by_service_name.return_value = matching_drafts
        api_client = mock.Mock(autospec=DataAPIClient)
        assert get_info_from_filename('12345-myservice-pricing-document.pdf', api_client, "g-cloud-12", "pdf") == (
            12345, 'pricingdocument', expected_result
        )

    def test_get_info_from_filename_cant_identify_document_type(self):
        api_client = mock.Mock()
        assert get_info_from_filename('12345-myservice.pdf', api_client, "g-cloud-12", "pdf") == (12345, None, None)


class TestUpdateDraftServiceWithDocumentPaths:

    def test_update_draft_service_with_document_paths_dry_run(self):
        assert update_draft_service_with_document_paths(
            "path/to/document", "pricingdocument", 12345, mock.Mock(), True
        )

    def test_update_draft_service_with_document_paths_valid_service(self):
        client = mock.Mock(autospec=DataAPIClient)
        client.get_draft_service.return_value = {'validationErrors': {}}

        assert update_draft_service_with_document_paths(
            "path/to/document", "pricingdocument", 12345, client, False
        )
        assert client.update_draft_service.call_args_list == [
            mock.call(12345, {'pricingDocumentURL': 'path/to/document'}, 'one off PDF upload script')
        ]
        assert client.get_draft_service.call_args_list == [
            mock.call(12345)
        ]

    def test_update_draft_service_with_document_paths_invalid_service(self):
        client = mock.Mock(autospec=DataAPIClient)
        client.get_draft_service.return_value = {'validationErrors': {'something': 'bad'}}

        assert update_draft_service_with_document_paths(
            "path/to/document", "pricingdocument", 12345, client, False
        ) is False

    def test_update_draft_service_with_document_paths_catches_exception_and_continues(self):
        client = mock.Mock(autospec=DataAPIClient)
        client.get_draft_service.side_effect = Exception('Boom')

        assert update_draft_service_with_document_paths(
            "path/to/document", "pricingdocument", 12345, client, False
        ) is False


@mock.patch('scripts.oneoff.upload_draft_service_pdfs.find_draft_id_by_service_name')
@mock.patch('scripts.oneoff.upload_draft_service_pdfs.update_draft_service_with_document_paths')
@mock.patch('scripts.oneoff.upload_draft_service_pdfs.upload_to_submissions_bucket')
@mock.patch('scripts.oneoff.upload_draft_service_pdfs.output_results')
@mock.patch('scripts.oneoff.upload_draft_service_pdfs.get_all_files_of_type')
class TestUploadDraftPDFsFromFolder:

    def setup(self):
        self.bucket = mock.Mock()
        self.client = mock.Mock(autospec=DataAPIClient)
        self.client.get_supplier.return_value = {"suppliers": {"name": "ACME LTD"}}

    @pytest.mark.parametrize('file_format', ('pdf', 'ods', 'odt', 'odp'))
    @pytest.mark.parametrize('dry_run', (True, False))
    def test_upload_draft_service_pdfs_from_folder_happy_path(
        self, get_all_files_of_type, output_results, upload_to_submissions_bucket,
        update_draft_service_with_document_paths, find_draft_id_by_service_name, dry_run, file_format
    ):
        get_all_files_of_type.return_value = [
            f'/path/to/555777-myservice-pricing-document.{file_format}',
            f'/path/to/555777-myservice-service-definition-document.{file_format}',
            f'/path/to/555777-myservice-terms-and-conditions.{file_format}',
        ]
        find_draft_id_by_service_name.return_value = 12345

        with freeze_time('2020-01-01'):
            upload_draft_service_pdfs_from_folder(
                self.bucket, "submissions", "https://assets.example.com",
                "~/local/folder", self.client, 'g-cloud-12', file_format, dry_run
            )

        assert get_all_files_of_type.call_args_list == [
            mock.call("~/local/folder", file_format)
        ]
        assert upload_to_submissions_bucket.call_args_list == [
            mock.call(
                f'12345-pricingdocument-2020-01-01-0000.{file_format}',
                self.bucket,
                "submissions",
                "g-cloud-12",
                555777,
                f'/path/to/555777-myservice-pricing-document.{file_format}',
                dry_run,
                {555777: "ACME LTD"}
            ),
            mock.call(
                f'12345-servicedefinitiondocument-2020-01-01-0000.{file_format}',
                self.bucket,
                "submissions",
                "g-cloud-12",
                555777,
                f'/path/to/555777-myservice-service-definition-document.{file_format}',
                dry_run,
                {555777: "ACME LTD"}
            ),
            mock.call(
                f'12345-termsandconditions-2020-01-01-0000.{file_format}',
                self.bucket,
                "submissions",
                "g-cloud-12",
                555777,
                f'/path/to/555777-myservice-terms-and-conditions.{file_format}',
                dry_run,
                {555777: "ACME LTD"}
            )
        ]
        assert update_draft_service_with_document_paths.call_args_list == [
            mock.call(
                "https://assets.example.com/suppliers/assets/g-cloud-12/submissions/"
                f"555777/12345-pricingdocument-2020-01-01-0000.{file_format}",
                "pricingdocument", 12345, self.client, dry_run
            ),
            mock.call(
                "https://assets.example.com/suppliers/assets/g-cloud-12/submissions/"
                f"555777/12345-servicedefinitiondocument-2020-01-01-0000.{file_format}",
                "servicedefinitiondocument", 12345, self.client, dry_run
            ),
            mock.call(
                "https://assets.example.com/suppliers/assets/g-cloud-12/submissions/"
                f"555777/12345-termsandconditions-2020-01-01-0000.{file_format}",
                "termsandconditions", 12345, self.client, dry_run
            )
        ]
        assert output_results.call_args_list == [
            # unidentifiable, successful, failed
            mock.call([], [12345, 12345, 12345], [])
        ]

    def test_upload_draft_service_pdfs_from_folder_unidentifiable_service(
        self, get_all_files_of_type, output_results, upload_to_submissions_bucket,
        update_draft_service_with_document_paths, find_draft_id_by_service_name
    ):
        get_all_files_of_type.return_value = [
            '/path/to/555777-myservice-pricing-document.pdf',
        ]
        find_draft_id_by_service_name.return_value = None

        with freeze_time('2020-01-01'):
            upload_draft_service_pdfs_from_folder(
                self.bucket, "submissions", "https://assets.example.com",
                "~/local/folder", self.client, 'g-cloud-12', 'pdf', False
            )

        assert get_all_files_of_type.call_args_list == [
            mock.call("~/local/folder", "pdf")
        ]
        assert upload_to_submissions_bucket.call_args_list == []
        assert update_draft_service_with_document_paths.call_args_list == []
        assert output_results.call_args_list == [
            # unidentifiable, successful, failed
            mock.call(['555777-myservice-pricing-document.pdf'], [], [])
        ]

    def test_upload_draft_service_pdfs_from_folder_invalid_service(
        self, get_all_files_of_type, output_results, upload_to_submissions_bucket,
        update_draft_service_with_document_paths, find_draft_id_by_service_name
    ):
        get_all_files_of_type.return_value = [
            '/path/to/555777-myservice-pricing-document.pdf',
        ]
        find_draft_id_by_service_name.return_value = 12345
        update_draft_service_with_document_paths.return_value = False

        upload_draft_service_pdfs_from_folder(
            self.bucket, "submissions", "https://assets.example.com",
            "~/local/folder", self.client, 'g-cloud-12', 'pdf', False
        )

        assert output_results.call_args_list == [
            # unidentifiable, successful, failed
            mock.call([], [], [12345])
        ]

    def test_upload_draft_service_pdfs_from_folder_invalid_file_format(
        self, get_all_files_of_type, output_results, upload_to_submissions_bucket,
        update_draft_service_with_document_paths, find_draft_id_by_service_name
    ):
        get_all_files_of_type.return_value = [
            '/path/to/555777-myservice-pricing-document.docx',
        ]
        find_draft_id_by_service_name.return_value = 12345
        update_draft_service_with_document_paths.return_value = False

        upload_draft_service_pdfs_from_folder(
            self.bucket, "submissions", "https://assets.example.com",
            "~/local/folder", self.client, 'g-cloud-12', 'docx', False
        )

        assert output_results.call_args_list == [
            # unidentifiable, successful, failed
            mock.call(['555777-myservice-pricing-document.docx'], [], [])
        ]
