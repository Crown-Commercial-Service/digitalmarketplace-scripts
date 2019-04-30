try:
    import __builtin__ as builtins
except ImportError:
    import builtins

from dmscripts.bulk_upload_documents import get_supplier_id_from_framework_file_path, upload_file, \
    get_document_name_from_file_path, get_supplier_name_dict_from_tsv
import mock
import pytest


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

    def test_get_supplier_id_from_framework_file_path_raises_if_cannot_find_id(self):
        with pytest.raises(ValueError):
            get_supplier_id_from_framework_file_path('no_id_present.pdf')


class TestGetDocumentNameFromFilePath:

    def test_get_document_name_from_file_path(self):
        path = '../../Downloads/Completed Frameworks BATCH2 SHARED WITH GDS/584425-result-letter.pdf'
        assert get_document_name_from_file_path(path) == 'result-letter.pdf'


class TestGetSupplierNameDictFromTSV:

    @mock.patch('dmscripts.bulk_upload_documents.csv')
    def test_get_supplier_name_dict_from_tsv(self, csv):
        csv.reader.return_value = [('584425', 'ICNT_Consulting_Ltd'), ('35435', 'Something')]
        with mock.patch.object(builtins, 'open', mock.mock_open()) as mock_open:
            assert get_supplier_name_dict_from_tsv('test.tsv') == {
                '35435': 'Something',
                '584425': 'ICNT_Consulting_Ltd'
            }
            assert mock_open.call_args_list == [mock.call('test.tsv', 'r')]

    def test_get_supplier_name_dict_from_tsv_requires_tsv_extension(self):
        with mock.patch.object(builtins, 'open', mock.mock_open()) as mock_open:
            assert get_supplier_name_dict_from_tsv('test.csv') is None
            assert mock_open.called is False

    def test_get_supplier_name_dict_from_tsv_doesnt_open_null_path(self):
        with mock.patch.object(builtins, 'open', mock.mock_open()) as mock_open:
            assert get_supplier_name_dict_from_tsv(None) is None
            assert mock_open.called is False


class TestUploadFile:

    def test_upload_file(self):
        file_path = '/92877-framework-agreement.pdf'
        bucket = mock.Mock()
        with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
            upload_file(bucket, False, file_path, 'g-cloud-11', 'agreements')
            assert bucket.save.call_count == 1
            bucket.save.assert_called_with(
                'g-cloud-11/agreements/92877/92877-framework-agreement.pdf',
                mock.ANY,
                acl='bucket-owner-full-control',
                download_filename=None)

    def test_upload_file_dry_run_doesnt_upload(self):
        file_path = '/92877-framework-agreement.pdf'
        bucket = mock.Mock()
        with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
            upload_file(bucket, True, file_path, 'g-cloud-11', 'agreements')
            assert bucket.save.call_count == 0

    def test_upload_file_with_document_bucket_category(self):
        file_path = '/92877-modern-slavery-statement.pdf'
        bucket = mock.Mock()
        with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
            upload_file(bucket, False, file_path, 'g-cloud-11', 'documents')
            assert bucket.save.call_count == 1
            bucket.save.assert_called_with(
                'g-cloud-11/documents/92877/92877-modern-slavery-statement.pdf',
                mock.ANY,
                acl='bucket-owner-full-control',
                download_filename=None)

    def test_upload_file_with_supplier_name_dictionary(self):
        file_path = '/35435-framework-agreement.pdf'
        supplier_name_dictionary = {'35435': 'Something', '584425': 'ICNT_Consulting_Ltd'}
        bucket = mock.Mock()
        with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
            upload_file(
                bucket, False, file_path, 'g-cloud-11', 'agreements', supplier_name_dict=supplier_name_dictionary
            )
            assert bucket.save.call_count == 1
            bucket.save.assert_called_with(
                'g-cloud-11/agreements/35435/35435-framework-agreement.pdf',
                mock.ANY,
                acl='bucket-owner-full-control',
                download_filename='Something-35435-framework-agreement.pdf')

    def test_upload_file_skips_signed_framework_agreement(self):
        file_path = '/12345-signed-framework-agreement.pdf'
        bucket = mock.Mock()
        with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')) as mock_open:
            with pytest.raises(ValueError):
                upload_file(bucket, False, file_path, 'g-cloud-11', 'agreements')
            assert bucket.save.call_count == 0
            assert mock_open.called is False
