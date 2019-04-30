import os
import tempfile
import shutil

from dmscripts.helpers.file_helpers import get_all_files_of_type


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
