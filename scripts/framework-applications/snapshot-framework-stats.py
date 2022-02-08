#!/usr/bin/env python3
"""
Fetch application stats for a given framework (suppliers, services and users) from the API.
Store the response in an audit event. Save the stats to the output file, if supplied. Email the stats, if supplied with
a Notify API key.

Usage:
    snapshot_framework_stats.py <stage> <framework_slug> [--outfile=filename] [--notify=notify_api_key]

Example:
    ./snapshot_framework_stats.py development g-cloud-12 --outfile=myfile.json
    ./snapshot_framework_stats.py development g-cloud-12
"""

from docopt import docopt
import json
import sys
import datetime

import dmapiclient
from dmapiclient.audit import AuditTypes

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.helpers.logging_helpers import configure_logger
from dmutils.env_helpers import get_api_endpoint_from_stage


logger = configure_logger()

NOTIFY_TEMPLATE_ID = "493ede76-d9c8-40b8-b543-1127ccb60674"  # In the 'Digital Marketplace CCS' service
STATS_EMAIL = "digitalmarketplace-stats@crowncommercial.gov.uk"


def get_human_readable_stats(stats):
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
            else:
                added_services += stat['count']
        else:
            if stat['declaration_status'] == 'complete':
                made_declaration += stat['count']
            else:
                started += stat['count']

    return (
        started,
        made_declaration,
        added_services,
        completed,
        total_applications,
    )


def log_human_readable_stats(stats):
    (
        started,
        made_declaration,
        added_services,
        completed,
        total_applications,
    ) = get_human_readable_stats(stats)

    logger.info("*********** STATS ***********")
    logger.info(f"Started: {started}")
    logger.info(f"Made declaration: {made_declaration}")
    logger.info(f"Added services: {added_services}")
    logger.info(f"Completed: {completed}")
    logger.info(f"Total applications: {total_applications}")
    logger.info("*****************************")


def email_stats(stats, mail_client, framework_name):
    (
        started,
        made_declaration,
        added_services,
        completed,
        total_applications,
    ) = get_human_readable_stats(stats)

    mail_client.send_email(
        STATS_EMAIL,
        NOTIFY_TEMPLATE_ID,
        personalisation={
            "started_count": started,
            "made_declaration_count": made_declaration,
            "added_services_count": added_services,
            "completed_count": completed,
            "total_count": total_applications,
            "framework_name": framework_name,
        }
    )


def snapshot_framework_stats(client, framework_slug):
    stats = client.get_framework_stats(framework_slug)
    client.create_audit_event(
        AuditTypes.snapshot_framework_stats,
        data=stats,
        object_type='frameworks',
        object_id=framework_slug
    )
    stats['date_generated'] = datetime.datetime.now().replace(microsecond=0).isoformat()
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
    if notify_api_key := arguments['--notify']:
        framework_name = client.get_framework(arguments['<framework_slug>'])['frameworks']['name']
        mail_client = scripts_notify_client(notify_api_key, logger=logger)

        email_stats(stats, mail_client, framework_name)
