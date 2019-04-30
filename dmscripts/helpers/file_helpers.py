import os


def get_all_files_of_type(local_directory, file_type):
    for root, subfolder, files in os.walk(local_directory):
        for filename in files:
            if filename.endswith(file_type):
                yield os.path.join(root, filename)
