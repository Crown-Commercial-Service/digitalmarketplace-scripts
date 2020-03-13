#!/usr/bin/env python3
"""
Fetches application stats for a given framework (suppliers, services and users) from the API.
The response is stored in an audit event and, if an ouput file is supplied, saved to a JSON file.

Usage:
    snapshot_framework_stats.py <stage> <framework_slug> [--outfile=filename]

Example:
    ./snapshot_framework_stats.py development g-cloud-12 --outfile=myfile.json
    ./snapshot_framework_stats.py development g-cloud-12
"""

from docopt import docopt
import json
import logging
import sys

import dmapiclient
from dmapiclient.audit import AuditTypes

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage


logger = logging.getLogger('script')
logging.basicConfig(level=logging.INFO)


def log_human_readable_stats(stats):
    total_applications = 0
    made_declaration = 0
    added_services = 0
    completed = 0
    started = 0

    for stat in stats['interested_suppliers']:
        total_applications += stat['count']
        if stat['has_completed_services']:
            if stat['declaration_status'] == 'complete':
                completed += stat['count']
            elif stat['declaration_status'] == 'started':
                added_services += stat['count']
        else:
            if stat['declaration_status'] == 'complete':
                made_declaration += stat['count']
            else:
                started += stat['count']

    logger.info("*********** STATS ***********")
    logger.info(f"Started: {started}")
    logger.info(f"Made declaration: {made_declaration}")
    logger.info(f"Added services: {added_services}")
    logger.info(f"Completed: {completed}")
    logger.info(f"Total applications: {total_applications}")
    logger.info("*****************************")


def snapshot_framework_stats(client, framework_slug):
    stats = client.get_framework_stats(framework_slug)
    client.create_audit_event(
        AuditTypes.snapshot_framework_stats,
        data=stats,
        object_type='frameworks',
        object_id=framework_slug
    )
    log_human_readable_stats(stats)

    logger.info("Framework stats snapshot saved as audit event")
    return stats


if __name__ == '__main__':
    arguments = docopt(__doc__)

    client = dmapiclient.DataAPIClient(
        get_api_endpoint_from_stage(arguments['<stage>']),
        get_auth_token('api', arguments['<stage>']),
    )
    stats = snapshot_framework_stats(client, arguments['<framework_slug>'])
    if arguments['--outfile'] is not None:
        with open(arguments['--outfile'], 'w') as outfile:
            json.dump(stats, outfile)
