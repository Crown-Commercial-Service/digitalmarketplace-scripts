#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sets supplier DOS status for all supplier IDs read from file. Each file line should contain one supplier ID.

Usage:
    scripts/update-dos-framework-results.py <stage> (--pass | --fail) --api-token=<data_api_token> <supplier_id_file>

Example:
    python scripts/update-dos-framework-results.py preview --pass --api-token=myToken 700000 700001

"""

import sys
sys.path.insert(0, '.')

import getpass

from docopt import docopt

from dmapiclient import DataAPIClient

from dmscripts.env import get_api_endpoint_from_stage
from dmscripts.logging import configure_logger
from dmscripts.insert_dos_framework_results import insert_result


logger = configure_logger()

if __name__ == '__main__':
    arguments = docopt(__doc__)

    data_api_url = get_api_endpoint_from_stage(arguments['<stage>'], 'api')
    client = DataAPIClient(data_api_url, arguments['--api-token'])
    user = getpass.getuser()
    result = True if arguments['--pass'] else False

    with open(arguments['<supplier_id_file>'], 'r') as f:
        supplier_ids = filter(None, [l.strip() for l in f.readlines()])

    for supplier_id in supplier_ids:
        logger.info(insert_result(client, supplier_id, result, user))
