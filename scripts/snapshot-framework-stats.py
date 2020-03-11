#!/usr/bin/env python3
"""Usage:
    snapshot_framework_stats.py <framework_slug> <stage>

Example:
    ./snapshot_framework_stats.py g-cloud-7 dev
"""

from docopt import docopt
import logging
import sys

import dmapiclient
from dmapiclient.audit import AuditTypes

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage


logger = logging.getLogger('script')
logging.basicConfig(level=logging.INFO)


def get_stats(data_client, framework_slug):
    return data_client.get_framework_stats(framework_slug)


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

    logger.info(f"Started: {started}")
    logger.info(f"Made declaration: {made_declaration}")
    logger.info(f"Added services: {added_services}")
    logger.info(f"Completed: {completed}")
    logger.info(f"Total applications: {total_applications}")


def snapshot_framework_stats(api_endpoint, api_token, framework_slug):
    data_client = dmapiclient.DataAPIClient(api_endpoint, api_token)

    stats = get_stats(data_client, framework_slug)
    data_client.create_audit_event(
        AuditTypes.snapshot_framework_stats,
        data=stats,
        object_type='frameworks',
        object_id=framework_slug
    )
    log_human_readable_stats(stats)

    logger.info("Framework stats snapshot saved")


if __name__ == '__main__':
    arguments = docopt(__doc__)

    snapshot_framework_stats(
        get_api_endpoint_from_stage(arguments['<stage>']),
        get_auth_token('api', arguments['<stage>']),
        arguments['<framework_slug>'],
    )
