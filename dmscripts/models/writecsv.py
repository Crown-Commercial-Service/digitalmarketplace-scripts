import os


def csv_path(output_dir, _filename):
    return os.path.join(output_dir, '{}.csv'.format(_filename))
