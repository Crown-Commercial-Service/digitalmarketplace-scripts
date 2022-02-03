#!/usr/bin/env python3
"""

For a DOS-type framework this will export details of all "user-research-studios" services.

Usage:
    scripts/export-dos-labs.py <stage> <framework_slug> [options]

Options:
    -v --verbose                Print INFO level messages.
    --output-dir=<output_dir>   Directory to write csv files to [default: output]
"""
import itertools
from multiprocessing.pool import ThreadPool
import os
import sys
sys.path.insert(0, '.')

import logging
from docopt import docopt
from dmapiclient import DataAPIClient

from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.framework_helpers import find_suppliers_with_details_and_draft_services
from dmscripts.helpers import logging_helpers
from dmscripts.export_dos_labs import append_contact_information_to_services
from dmutils.env_helpers import get_api_endpoint_from_stage

if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv

REQUIRED_CONTACT_DETAILS_KEYS = ['email', 'contactName', 'phoneNumber']


def find_all_labs(client, map_impl=map):
    records = find_suppliers_with_details_and_draft_services(client,
                                                             FRAMEWORK_SLUG,
                                                             lot="user-research-studios",
                                                             statuses="submitted",
                                                             map_impl=map_impl,
                                                             )
    records = list(filter(lambda record: record['onFramework'], records))
    records = append_contact_information_to_services(records, REQUIRED_CONTACT_DETAILS_KEYS)
    services = itertools.chain.from_iterable(record['services'] for record in records)
    return services


def write_labs_csv(services, filename, logger=None):
    writer = None
    bad_fields = ['links']
    logger.info("Building CSV for User Research Studios")

    with open(filename, "w+") as f:
        for service in services:
            service = {key: value for key, value in service.items() if key not in bad_fields}
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=sorted(service.keys()))
                writer.writeheader()
            writer.writerow(service)


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    FRAMEWORK_SLUG = arguments['<framework_slug>']
    OUTPUT_DIR = arguments['--output-dir']
    verbose = arguments['--verbose']

    logger = logging_helpers.configure_logger(
        {"dmapiclient": logging.INFO} if verbose else {"dmapiclient": logging.WARN}
    )

    if not os.path.exists(OUTPUT_DIR):
        logger.info("Creating {} directory".format(OUTPUT_DIR))
        os.makedirs(OUTPUT_DIR)

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), get_auth_token('api', STAGE))

    pool = ThreadPool(3)

    logger.info(f"Finding suppliers for User Research Studios on {FRAMEWORK_SLUG}")
    write_labs_csv(
        find_all_labs(client, map_impl=pool.imap),
        os.path.join(OUTPUT_DIR, "user-research-studios.csv"),
        logger=logger
    )
