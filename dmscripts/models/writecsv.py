import sys
import os
if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv


def csv_path(output_dir, _filename):
    return os.path.join(output_dir, '{}.csv'.format(_filename))


def write_csv(filename, models, keys=None):
    if keys is None:
        keys = sorted(models[0].keys())

    keys = [k[len(k)-1] if isinstance(k, (tuple, list)) else k for k in keys]

    csv_writer = csv.DictWriter(
        open(filename, 'w+'),
        fieldnames=keys,
        delimiter=',',
        lineterminator='\n',
        quotechar='"'
    )
    csv_writer.writeheader()
    for m in models:
        csv_writer.writerow(m)
