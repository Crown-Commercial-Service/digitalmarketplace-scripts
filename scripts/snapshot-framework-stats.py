#!/usr/bin/env python3
"""Usage:
    snapshot_framework_stats.py <stage> <framework_slug> <filename>

Example:
    ./snapshot_framework_stats.py production g-cloud-12 myfile.json
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


def snapshot_framework_stats(client, framework_slug):
    stats = client.get_framework_stats(framework_slug)
    client.create_audit_event(
        AuditTypes.snapshot_framework_stats,
        data=stats,
        object_type='frameworks',
        object_id=framework_slug
    )

    logger.info("Framework stats snapshot saved as audit event")
    return stats


if __name__ == '__main__':
    arguments = docopt(__doc__)
    client = dmapiclient.DataAPIClient(
        get_api_endpoint_from_stage(arguments['<stage>']),
        get_auth_token('api', arguments['<stage>']),
    )
    stats = snapshot_framework_stats(client, arguments['<framework_slug>'])
    with open(arguments['<filename>'], 'w') as outfile:
        json.dump(stats, outfile)
