#!/usr/bin/env python
"""
A one-off script for getting stats to help estimate traffic for the DOS 5 close of applications
"""

import sys
import dmapiclient

sys.path.insert(0, '.')

from dmutils.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers.auth_helpers import get_auth_token


if __name__ == '__main__':
    stage = 'production'
    data = dmapiclient.DataAPIClient(
        get_api_endpoint_from_stage(stage),
        get_auth_token('api', stage),
    )

    frameworks = [
        'g-cloud-7',
        'g-cloud-8',
        'g-cloud-9',
        'g-cloud-10',
        'g-cloud-11',
        'g-cloud-12',
        'digital-outcomes-and-specialists',
        'digital-outcomes-and-specialists-2',
        'digital-outcomes-and-specialists-3',
        'digital-outcomes-and-specialists-4',
        'digital-outcomes-and-specialists-5',
    ]

    framework_stats = {f: data.get_framework_stats(f) for f in frameworks}

    for framework, stats in framework_stats.items():
        try:
            [completed_suppliers] = [
                s['count'] for s in stats['interested_suppliers']
                if s['declaration_status'] == 'complete' and s['has_completed_services']
            ]
        except ValueError:
            continue

        print(f"{framework} suppliers: {completed_suppliers}")

    for framework, stats in framework_stats.items():
        submitted_services = [s for s in stats['services'] if s['declaration_made'] and s['status'] == 'submitted']

        total_submitted = sum(s['count'] for s in submitted_services)

        if total_submitted:
            print(f"{framework} submitted services: {total_submitted}")
