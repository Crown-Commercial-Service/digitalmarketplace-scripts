#!/usr/bin/env python
"""Generate data export CSVs

Load model data from the API or the existing CSV, process it according
to the rules defined in the CONFIG and store the output in the CSV.

CSV files are read from and saved to `<output-dir>/<model>.csv`

If called without a model name the script will dump all defined models.

Usage:
    scripts/get-model-data.py [options] <stage> <api_token> [<model>...]

Options:
    -h --help       Show this screen.
    -v --verbose    Print apiclient INFO messages.
    --limit=<limit>  Limit the number of items exported
    --output-dir=<output_dir>  Directory to write csv files to [default: data]

Arguments:

    models:
        buyer_users
        supplier_users
        dos_services
        briefs
        brief_responses
        successful_brief_responses
        brief_responses_summary

"""

import os
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmapiclient import DataAPIClient
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.models.process_rules import format_datetime_string_as_date, remove_username_from_email_address
from dmscripts.models.writecsv import csv_path
from dmscripts.models import queries

from dmscripts.helpers.logging_helpers import logging, configure_logger

DOS_SPECIALIST_ROLES = [
    "agileCoach",
    "businessAnalyst",
    "communicationsManager",
    "contentDesigner",
    "securityConsultant",
    "deliveryManager",
    "designer",
    "developer",
    "performanceAnalyst",
    "portfolioManager",
    "productManager",
    "programmeManager",
    "qualityAssurance",
    "serviceManager",
    "technicalArchitect",
    "userResearcher",
    "webOperations"
]
DOS_SPECIALIST_ROLES_PRICE_MAX = [s + 'PriceMax' for s in DOS_SPECIALIST_ROLES]

CONFIGS = [
    {
        'name': 'buyer_users',
        'base_model': 'users',
        'keys': ('id', 'emailAddress', 'createdAt', 'role'),
        'get_data_kwargs': {},
        'process_fields': {
            'emailAddress': remove_username_from_email_address,
            'createdAt': format_datetime_string_as_date,
        },
        'filter_query': "role == 'buyer' and createdAt >= '2016-04-25'",
        'sort_by': 'createdAt'
    },
    {
        'name': 'supplier_users',
        'base_model': 'users',
        'keys': ('id', ('supplier', 'supplierId'), 'createdAt', 'role'),
        'get_data_kwargs': {},
        'process_fields': {
            'createdAt': format_datetime_string_as_date
        },
        'filter_query': "role == 'supplier' and createdAt >= '2016-04-25'",
        'sort_by': ['createdAt', 'id']
    },
    {
        'name': 'dos_services',
        'base_model': 'services',
        'get_data_kwargs': {'framework': 'digital-outcomes-and-specialists, digital-outcomes-and-specialists-2'},
        'keys': (
            [
                'id',
                'frameworkSlug',
                'lotSlug',
                'status',
                'supplierId',
                'supplierName'
            ] + DOS_SPECIALIST_ROLES_PRICE_MAX  # We use price max as a proxy for a service having a role
        ),
        'process_fields': {
            role: bool for role in DOS_SPECIALIST_ROLES_PRICE_MAX
        },
        'rename_fields': dict(list(zip(DOS_SPECIALIST_ROLES_PRICE_MAX, DOS_SPECIALIST_ROLES))),
        'sort_by': ['frameworkSlug', 'supplierId', 'lotSlug']
    },
    {
        'name': 'g_cloud_services',
        'base_model': 'services',
        'get_data_kwargs': {'framework': 'g-cloud-8, g-cloud-9'},
        'keys': (
            [
                'id',
                'frameworkSlug',
                'lotSlug',
                'serviceName',
                'status',
                'supplierId',
                'supplierName'
            ]
        ),
        'sort_by': ['frameworkSlug', 'supplierId', 'lotSlug']
    },
    {
        'name': 'briefs',
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
            'specialistRole',
            'clarificationQuestions',
            'frameworkSlug',
            'budgetRange',
            'startDate',
            'contractLength',
            'isACopy',
            'awardedBriefResponseId'
        ),
        'get_data_kwargs': {'with_users': 'true'},
        'process_fields': {
            'createdAt': format_datetime_string_as_date,
            'publishedAt': format_datetime_string_as_date,
            'emailAddress': remove_username_from_email_address,
            'clarificationQuestions': len,
        },
        'sort_by': 'createdAt'
    },
    {
        'name': 'brief_responses',
        'base_model': 'brief_responses',
        'keys': (
            'briefId',
            'supplierId',
            'createdAt',
            'supplierName',
            'submittedAt',
            'essentialRequirements',
            'id',
            'awardedContractStartDate',
            'awardedContractValue',
            'supplierOrganisationSize',
            'status',
        ),
        'assign_json_subfields': {
            'awardDetails': ['awardedContractStartDate', 'awardedContractValue'],
            'brief': ['title', 'frameworkSlug'],
        },
        'get_data_kwargs': {},
        'process_fields': {
            'createdAt': format_datetime_string_as_date,
            'submittedAt': format_datetime_string_as_date,
            'essentialRequirements': all,
        },
        'sort_by': ['briefId', 'submittedAt']
    },
    {
        'name': 'successful_brief_responses',
        'model': 'brief_responses',
        'joins': [
            {
                'model': 'briefs',
                'left_on': 'briefId',
                'right_on':'id',
                'data_duplicate_suffix': 'briefs'
            }
        ],
        'filter_query': "essentialRequirements",
        'keys': (
            'briefId',
            'lot',
            'title',
            'supplierId',
            'supplierName',
            'submittedAt',
            'status',
            'awardedBriefResponseId',
            'awardedContractStartDate',
            'awardedContractValue',
            'supplierOrganisationSize'
        ),
        'sort_by': ['briefId', 'submittedAt']
    },
    {
        'name': 'brief_responses_summary',
        'model': 'briefs',
        'add_counts': {
            'model': 'brief_responses',
            'join': ('id', 'briefId'),
            'group_by': 'essentialRequirements'
        },
        'filter_query': "status in ['live', 'closed', 'awarded', 'withdrawn', 'cancelled', 'unsuccessful']",
        'keys': (
            'id',
            'lot',
            'title',
            'status',
            'essentialRequirements-False',
            'essentialRequirements-True',
            'clarificationQuestions',
            'frameworkSlug',
            'specialistRole',
            'awardedBriefResponseId'
        ),
        'sort_by': ['id']
    },
    {
        'name': 'awarded_brief_responses',
        'model': 'brief_responses',
        'filter_query': 'status == "awarded"',
        'keys': (
            'briefId',
            'awardedContractStartDate',
            'awardedContractValue',
            'supplierOrganisationSize',
            'supplierName'
        ),
        'sort_by': ['briefId']
    },
]

if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    API_TOKEN = arguments['<api_token>']
    OUTPUT_DIR = arguments['--output-dir']
    MODELS = arguments['<model>']

    logging_config = {'dmapiclient': logging.INFO} if bool(arguments.get('--verbose')) \
        else {'dmapiclient': logging.WARNING}
    logger = configure_logger(logging_config)

    if not os.path.exists(OUTPUT_DIR):
        logger.info("Creating {} directory".format(OUTPUT_DIR))
        os.makedirs(OUTPUT_DIR)

    MODELS = set(MODELS if MODELS else [config['name'] for config in CONFIGS])

    limit = int(arguments.get('--limit')) if arguments.get('--limit') else None

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), API_TOKEN)

    for config in CONFIGS:
        # Skip CSVs that weren't requested
        if config['name'] not in MODELS:
            continue
        logger.info('Processing {} data'.format(config['name']))

        if 'base_model' in config:
            required_keys = list(config['keys']) + list(config.get('assign_json_subfields', {}).keys())
            data = queries.base_model(config['base_model'], required_keys, config['get_data_kwargs'],
                                      client=client, logger=logger, limit=limit)
        elif 'model' in config:
            data = queries.model(config['model'], directory=OUTPUT_DIR)
        if 'joins' in config:
            for join in config['joins']:
                data = queries.join(data, directory=OUTPUT_DIR, **join)

        # transform values that we want to transform
        if 'assign_json_subfields' in config:
            for field, subfields in config['assign_json_subfields'].items():
                data = queries.assign_json_subfields(field, subfields, data)

        if 'add_counts' in config:
            data = queries.add_counts(data=data, directory=OUTPUT_DIR, **config['add_counts'])
        if 'aggregation_counts' in config:
            for count in config['aggregation_counts']:
                data = queries.add_aggregation_counts(data=data, **count)

        if 'filter_query' in config:
            # filter out things we don't want
            data = queries.filter_rows(config['filter_query'], data)
            logger.info(
                '{} {} remaining after filtering'.format(len(data), config['name'])
            )

        # Only keep requested keys in the output CSV
        keys = [
            k[-1] if isinstance(k, (tuple, list)) else k
            for k in config['keys']
            if (k[-1] if isinstance(k, (tuple, list)) else k) in data
        ]
        data = data[keys]
        if 'process_fields' in config:
            data = queries.process_fields(config['process_fields'], data)
        if 'rename_fields' in config:
            data = queries.rename_fields(config['rename_fields'], data)

        # sort list by some dict value
        if 'sort_by' in config:
            data = queries.sort_by(config['sort_by'], data)

        # write up your CSV
        filename = csv_path(OUTPUT_DIR, config['name'])
        data.to_csv(filename, index=False, encoding='utf-8')
        logger.info('Printed `{}` with {} rows'.format(filename, len(data)))
