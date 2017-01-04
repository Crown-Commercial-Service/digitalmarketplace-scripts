import sys
import os
if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv


def csv_path(output_dir, _filename):
    return os.path.join(output_dir, '{}.csv'.format(_filename))
