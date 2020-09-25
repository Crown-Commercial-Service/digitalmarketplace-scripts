#!/usr/bin/env python

import argparse
import multiprocessing as mp
from multiprocessing.pool import ThreadPool
import sys

from dmapiclient.audit import AuditTypes
from dmapiclient.data import DataAPIClient

sys.path.insert(0, '.')

from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage


ACKNOWLEDGE_USER = 'scripts/oneoff/acknowledge_publish_draft_service_updates.py'


def acknowledge_update(audit_event):
    response = data.acknowledge_audit_event(audit_event['id'], user=ACKNOWLEDGE_USER)['auditEvents']
    print(f'Acknowledged {audit_event["id"]} on service id #{audit_event["data"]["serviceId"]} by '
          f'supplier `{audit_event["data"]["supplierName"]}`: {response["acknowledged"]}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', default='development', choices=['development', 'preview', 'staging', 'production'],
                        help="Which stage's API to communicate with.")
    parser.add_argument('date', type=str, help='The date on which the updates occurred, used to filter audit events '
                                               '(YYYY-MM-DD).')
    args = parser.parse_args()

    data = DataAPIClient(get_api_endpoint_from_stage(args.stage), get_auth_token('api', args.stage))

    audit_events = data.find_audit_events_iter(audit_type=AuditTypes.update_service,
                                               user='publish_draft_services.py',
                                               audit_date=args.date,
                                               acknowledged='false')

    # Need to slurp them all into memory, or the ThreadPool loses track of some of them.
    print('Retrieving audit events ...')
    audit_events = [audit_event for audit_event in audit_events]

    # Significantly IO bound, so use threads - and no reason not to use plenty of them.
    pool = ThreadPool(processes=mp.cpu_count() * 2)

    count = 0
    for x in pool.imap(acknowledge_update, audit_events):
        count += 1

    pool.close()
    pool.join()

    print(f'All done - acknowledged {count} audit events')
