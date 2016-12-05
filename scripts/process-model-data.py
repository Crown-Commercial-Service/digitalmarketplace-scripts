#!/usr/bin/env python3
"""Process CSV model data, e.g. for aggregation or merging

Usage:
    scripts/process-model-data.py [-h] <query-name> <csv-dir>

Options:
    -h --help       Show this screen.
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
import pandas as pd
import os.path

from dmscripts.models import queries


CONFIG = {
    'successful_supplier_applications': queries.successful_supplier_applications
}


def get_query(query_name):
    query_func = CONFIG.get(query_name)
    if query_func is None:
        raise ValueError('{} is not a defined query.'.format(query_name))
    return query_func

if __name__ == '__main__':
    arguments = docopt(__doc__)

    CSV_DIR = arguments['<csv-dir>']
    QUERY_NAME = arguments['<query-name>']

    query = get_query(QUERY_NAME)
    data_frames = dict()
    # query params give us the table (data frame) names we need...
    for data_frame_name in query.__code__.co_varnames[:query.__code__.co_argcount]:
        # assume each name corresponds to a csv file in csv-dir - this may be a stretch
        filespec = os.path.join(CSV_DIR, '{}.csv'.format(data_frame_name))
        data_frames[data_frame_name] = pd.read_csv(filespec)

    result = query(**data_frames)

    outfilespec = os.path.join(CSV_DIR, '{}.csv'.format(QUERY_NAME))
    result.to_csv(outfilespec, index=False)
