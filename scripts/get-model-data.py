#!/usr/bin/env python3
"""Export a CSV of all models or something

Looks for a corresponding find_{model}_iter() method in the api client and returns
all of the results in a CSV with only requested keys being used as columns
Before generating the final csv, it is possible to:
- filter the list, looking for only those entries with a particular value
- do some additional processing on a value
- sort the list

Usage:
    scripts/get-model-data.py [-h] <stage> <api_token> <model> <output_dir> [--limit=<limit>][-v]

Options:
    -h --help       Show this screen.
    -v --verbose    Print apiclient INFO messages.
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmapiclient import DataAPIClient
from dmscripts.env import get_api_endpoint_from_stage
from dmscripts.models.modeltrawler import ModelTrawler
from dmscripts.models.utils import process_collection, return_filtered_collection, return_sorted_collection
from dmscripts.models.process_rules import format_datetime_string_as_date, remove_username_from_email_address
from dmscripts.models.writecsv import csv_path, write_csv

from dmscripts import logging


CONFIGS = {
    'buyers': {
        'base_model': 'users',
        'keys': ('id', 'emailAddress', 'createdAt', 'role'),
        'get_data_kwargs': {},
        'process_rules': {
            'emailAddress': remove_username_from_email_address,
            'createdAt': format_datetime_string_as_date,
        },
        'filter_rules': [
            ('role', '==', 'buyer'),
            ('createdAt', '>=', '2016-04-25')
        ],
        'sort_by': 'createdAt'
    },
    'suppliers': {
        'base_model': 'users',
        'keys': ('id', ('supplier', 'supplierId'), 'createdAt', 'role'),
        'get_data_kwargs': {},
        'process_rules': {
            'createdAt': format_datetime_string_as_date
        },
        'filter_rules': [
            ('role', '==', 'supplier'),
            ('createdAt', '>=', '2016-04-25')
        ],
        'sort_by': 'createdAt'
    },
    'briefs': {
        'base_model': 'briefs',
        'keys': (
            'id',
            'createdAt',
            'lot',
            'title',
            'organisation',
            ('users', 0, 'emailAddress'),
            'location',
            'status',
            'publishedAt',
            'requirementsLength',
            'specialistRole'
        ),
        'get_data_kwargs': {'with_users': 'true'},
        'process_rules': {
            'createdAt': format_datetime_string_as_date,
            'publishedAt': format_datetime_string_as_date,
            'emailAddress': remove_username_from_email_address,
        },
        'filter_rules': [],
        'sort_by': 'createdAt'
    },
    'brief_responses': {
        'base_model': 'brief_responses',
        'keys': (
            'briefId',
            'supplierId',
            'createdAt'
        ),
        'get_data_kwargs': {},
        'process_rules': {
            'createdAt': format_datetime_string_as_date,
        },
        'filter_rules': [],
        'sort_by': 'createdAt'
    }
}

if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    API_TOKEN = arguments['<api_token>']
    OUTPUT_DIR = arguments['<output_dir>']
    MODEL = arguments['<model>']

    limit = int(arguments.get('--limit')) if arguments.get('--limit') else None
    logging_config = {'dmapiclient': logging.INFO} if bool(arguments.get('--verbose')) \
        else {'dmapiclient': logging.WARNING}
    logger = logging.configure_logger(logging_config)

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), API_TOKEN)
    config = CONFIGS[MODEL]

    mt = ModelTrawler(config['base_model'], client)

    # run stuff
    data = list(mt.get_data(keys=config['keys'], limit=limit, **config['get_data_kwargs']))
    logger.info('{} {} returned after {}s'.format(len(data), config['base_model'], mt.get_time_running()))

    # filter out things we don't want
    data = return_filtered_collection(config['filter_rules'], data)
    if 'filter_rules' in config and config['filter_rules']:
        logger.info('{} {} remaining after filtering collection'.format(len(data), config['base_model']))

    # transform values that we want to transform
    process_collection(config['process_rules'], data)

    # sort list by some dict value
    data = return_sorted_collection(config['sort_by'], data)

    # write up your CSV
    filename = csv_path(OUTPUT_DIR, MODEL)
    write_csv(filename, data, keys=config['keys'])
    logger.info('Printed `{}` with {} rows'.format(filename, len(data)))
