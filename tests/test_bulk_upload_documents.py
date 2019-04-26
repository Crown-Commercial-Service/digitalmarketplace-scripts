import os
import tempfile
import shutil

try:
    import __builtin__ as builtins
except ImportError:
    import builtins

from dmscripts.bulk_upload_documents import get_bucket_name, get_all_files_of_type, \
    get_supplier_id_from_framework_file_path, upload_file, get_document_name_from_file_path, \
    get_supplier_name_dict_from_tsv
import mock
import pytest


class TestGetBucketName:

    @pytest.mark.parametrize(
        'stage, expected_bucket_name',
        [
            ('local', 'digitalmarketplace-dev-uploads'),
            ('dev', 'digitalmarketplace-dev-uploads'),
            ('preview', 'digitalmarketplace-agreements-preview-preview'),
            ('staging', 'digitalmarketplace-agreements-staging-staging'),
            ('production', 'digitalmarketplace-agreements-production-production'),
        ]
    )
    def test_get_bucket_name_for_agreements_documents(self, stage, expected_bucket_name):
        assert get_bucket_name(stage, 'agreements') == expected_bucket_name

    def test_get_bucket_name_returns_none_for_invalid_stage(self):
        assert get_bucket_name('xanadu', 'agreements') is None

    def test_get_bucket_name_returns_none_for_invalid_bucket_category(self):
        assert get_bucket_name('local', 'bananas') is None


class TestGetAllFilesOfType:

    def test_get_all_files_of_type_for_flat_folder(self):
        temp_folder_path = tempfile.mkdtemp()
        pdf1 = open(os.path.join(temp_folder_path, 'test1.pdf'), 'w+')
        pdf2 = open(os.path.join(temp_folder_path, 'test2.pdf'), 'w+')
        assert len(list(get_all_files_of_type(temp_folder_path, 'pdf'))) == 2
        pdf1.close()
        pdf2.close()
        shutil.rmtree(temp_folder_path)

    def test_get_all_files_of_type_for_nested_folder(self):
        temp_folder_path = tempfile.mkdtemp()
        pdf1 = open(os.path.join(temp_folder_path, 'test1.pdf'), 'w+')
        nested_temp_folder_path = tempfile.mkdtemp(dir=temp_folder_path)
        pdf2 = open(os.path.join(nested_temp_folder_path, 'test2.pdf'), 'w+')
        assert len(list(get_all_files_of_type(temp_folder_path, 'pdf'))) == 2
        pdf1.close()
        pdf2.close()
        shutil.rmtree(temp_folder_path)


class TestGetSupplierIDFromFrameworkFilePath:

    @pytest.mark.parametrize(
        'path',
        [
            '../../Downloads/Completed Frameworks BATCH2 SHARED WITH GDS/ICNT_Consulting_Ltd-584425-signed-framework-agreement.pdf'  # noqa
            '../../Downloads/Completed Frameworks BATCH2 SHARED WITH GDS/ICNT_Consulting_Ltd-584425_signed_framework_agreement.pdf'  # noqa
            '../../Downloads/Completed Frameworks BATCH2 SHARED WITH GDS/584425-result-letter.pdf'
        ]
    )
    def test_get_supplier_id_from_framework_file_path_for_file(self, path):
        assert get_supplier_id_from_framework_file_path(path) == '584425'


class TestGetDocumentNameFromFilePath:

    def test_get_document_name_from_file_path(self):
        path = '../../Downloads/Completed Frameworks BATCH2 SHARED WITH GDS/584425-result-letter.pdf'
        assert get_document_name_from_file_path(path) == 'result-letter.pdf'


class TestGetSupplierNameDictFromTSV:

    @mock.patch('dmscripts.bulk_upload_documents.csv')
    def test_get_supplier_name_dict_from_tsv(self, csv):
        csv.reader.return_value = [('584425', 'ICNT_Consulting_Ltd'), ('35435', 'Something')]
        with mock.patch.object(builtins, 'open', mock.mock_open()):
            assert get_supplier_name_dict_from_tsv('test_csv.pdf') == {'35435': 'Something', '584425': 'ICNT_Consulting_Ltd'}  # noqa


class TestUploadFile:

    def test_upload_file(self):
        file_path = 'The_Business_Software_Centre-92877-signed-framework-agreement.pdf'
        bucket = mock.Mock()
        with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
            upload_file(bucket, False, file_path, 'g-cloud-7', 'agreements', 'countersigned_agreement', 'pdf')
            assert bucket.save.call_count == 1
            bucket.save.assert_called_with(
                'g-cloud-7/agreements/92877/92877-countersigned_agreement.pdf',
                mock.ANY,
                acl='bucket-owner-full-control',
                download_filename=None)

    def test_upload_file_dry_run_doesnt_upload(self):
        file_path = 'The_Business_Software_Centre-92877-signed-framework-agreement.pdf'
        bucket = mock.Mock()
        with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
            upload_file(bucket, True, file_path, 'g-cloud-7', 'agreements', 'countersigned_agreement', 'pdf')
            assert bucket.save.call_count == 0

    def test_upload_file_without_document_category(self):
        file_path = '/92877-framework-agreement.pdf'
        bucket = mock.Mock()
        with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
            upload_file(bucket, False, file_path, 'g-cloud-7', 'agreements')
            assert bucket.save.call_count == 1
            bucket.save.assert_called_with(
                'g-cloud-7/agreements/92877/92877-framework-agreement.pdf',
                mock.ANY,
                acl='bucket-owner-full-control',
                download_filename=None)

    def test_upload_file_with_supplier_name_dictionary(self):
        file_path = '/35435-framework-agreement.pdf'
        supplier_name_dictionary = {'35435': 'Something', '584425': 'ICNT_Consulting_Ltd'}
        bucket = mock.Mock()
        with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
            upload_file(bucket, False, file_path, 'g-cloud-7', 'agreements', supplier_name_dict=supplier_name_dictionary)  # noqa
            assert bucket.save.call_count == 1
            bucket.save.assert_called_with(
                'g-cloud-7/agreements/35435/35435-framework-agreement.pdf',
                mock.ANY,
                acl='bucket-owner-full-control',
                download_filename='Something-35435-framework-agreement.pdf')
