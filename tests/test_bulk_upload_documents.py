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


def test_get_bucket_name_for_agreements_documents():
    assert get_bucket_name('dev', 'agreements') == 'digitalmarketplace-agreements-dev-dev'  # noqa
    assert get_bucket_name('preview', 'agreements') == 'digitalmarketplace-agreements-preview-preview'  # noqa
    assert get_bucket_name('staging', 'agreements') == 'digitalmarketplace-agreements-staging-staging'  # noqa


def test_get_all_files_of_type_for_flat_folder():
    temp_folder_path = tempfile.mkdtemp()
    pdf1 = open(os.path.join(temp_folder_path, 'test1.pdf'), 'w+')
    pdf2 = open(os.path.join(temp_folder_path, 'test2.pdf'), 'w+')
    assert len(list(get_all_files_of_type(temp_folder_path, 'pdf'))) == 2
    pdf1.close()
    pdf2.close()
    shutil.rmtree(temp_folder_path)


def test_get_all_files_of_type_for_nested_folder():
    temp_folder_path = tempfile.mkdtemp()
    pdf1 = open(os.path.join(temp_folder_path, 'test1.pdf'), 'w+')
    nested_temp_folder_path = tempfile.mkdtemp(dir=temp_folder_path)
    pdf2 = open(os.path.join(nested_temp_folder_path, 'test2.pdf'), 'w+')
    assert len(list(get_all_files_of_type(temp_folder_path, 'pdf'))) == 2
    pdf1.close()
    pdf2.close()
    shutil.rmtree(temp_folder_path)


def test_get_supplier_id_from_framework_file_path_for_file_with_dashes():
    path = '../../Downloads/Completed Frameworks BATCH2 SHARED WITH GDS/ICNT_Consulting_Ltd-584425-signed-framework-agreement.pdf'  # noqa
    assert get_supplier_id_from_framework_file_path(path) == '584425'


def test_get_supplier_id_from_framework_file_path_for_file_with_underscores():
    path = '../../Downloads/Completed Frameworks BATCH2 SHARED WITH GDS/ICNT_Consulting_Ltd-584425_signed_framework_agreement.pdf'  # noqa
    assert get_supplier_id_from_framework_file_path(path) == '584425'


def test_get_supplier_id_from_framework_file_path_for_file_starting_with_supplier_id():
    path = '../../Downloads/Completed Frameworks BATCH2 SHARED WITH GDS/584425-result-letter.pdf'  # noqa
    assert get_supplier_id_from_framework_file_path(path) == '584425'


def test_get_document_name_from_file_path():
    path = '../../Downloads/Completed Frameworks BATCH2 SHARED WITH GDS/584425-result-letter.pdf'  # noqa
    assert get_document_name_from_file_path(path) == 'result-letter.pdf'


@mock.patch('dmscripts.bulk_upload_documents.csv')
def test_get_supplier_name_dict_from_tsv(csv):
    csv.reader.return_value = [('584425', 'ICNT_Consulting_Ltd'), ('35435', 'Something')]
    with mock.patch.object(builtins, 'open', mock.mock_open()):
        assert get_supplier_name_dict_from_tsv('test_csv.pdf') == {'35435': 'Something', '584425': 'ICNT_Consulting_Ltd'}  # noqa


def test_upload_file():
    file_path = 'The_Business_Software_Centre-92877-signed-framework-agreement.pdf'
    bucket = mock.Mock()
    with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
        upload_file(bucket, False, file_path, 'g-cloud-7', 'agreements',
                    'countersigned_agreement', 'pdf')
        assert bucket.save.call_count == 1
        bucket.save.assert_called_with(
            'g-cloud-7/agreements/92877/92877-countersigned_agreement.pdf',
            mock.ANY,
            acl='private',
            download_filename=None)


def test_upload_file_dry_run_doesnt_upload():
    file_path = 'The_Business_Software_Centre-92877-signed-framework-agreement.pdf'
    bucket = mock.Mock()
    with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
        upload_file(bucket, True, file_path, 'g-cloud-7', 'agreements',
                    'countersigned_agreement', 'pdf')
        assert bucket.save.call_count == 0


def test_upload_file_without_document_category():
    file_path = '/92877-framework-agreement.pdf'
    bucket = mock.Mock()
    with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
        upload_file(bucket, False, file_path, 'g-cloud-7', 'agreements')
        assert bucket.save.call_count == 1
        bucket.save.assert_called_with(
            'g-cloud-7/agreements/92877/92877-framework-agreement.pdf',
            mock.ANY,
            acl='private',
            download_filename=None)


def test_upload_file_with_supplier_name_dictionary():
    file_path = '/35435-framework-agreement.pdf'
    supplier_name_dictionary = {'35435': 'Something', '584425': 'ICNT_Consulting_Ltd'}
    bucket = mock.Mock()
    with mock.patch.object(builtins, 'open', mock.mock_open(read_data='foo')):
        upload_file(bucket, False, file_path, 'g-cloud-7', 'agreements', supplier_name_dict=supplier_name_dictionary)  # noqa
        assert bucket.save.call_count == 1
        bucket.save.assert_called_with(
            'g-cloud-7/agreements/35435/35435-framework-agreement.pdf',
            mock.ANY,
            acl='private',
            download_filename='Something-35435-framework-agreement.pdf')
