#!/usr/bin/env python
"""Usage:
    snapshot_framework_stats.py <framework_slug> <stage> <api_token>

Example:
    ./snapshot_framework_stats.py g-cloud-7 dev myToken
"""

import backoff
from docopt import docopt
import logging
import sys

import dmapiclient
from dmapiclient.audit import AuditTypes

sys.path.insert(0, '.')
from dmutils.env_helpers import get_api_endpoint_from_stage


logger = logging.getLogger('script')
logging.basicConfig(level=logging.INFO)


@backoff.on_exception(backoff.expo, dmapiclient.HTTPError, max_tries=5)
def get_stats(data_client, framework_slug):
    return data_client.get_framework_stats(framework_slug)


def snapshot_framework_stats(api_endpoint, api_token, framework_slug):
    data_client = dmapiclient.DataAPIClient(api_endpoint, api_token)

    stats = get_stats(data_client, framework_slug)
    data_client.create_audit_event(
        AuditTypes.snapshot_framework_stats,
        data=stats,
        object_type='frameworks',
        object_id=framework_slug
    )

    logger.info("Framework stats snapshot saved")


if __name__ == '__main__':
    arguments = docopt(__doc__)

    snapshot_framework_stats(
        get_api_endpoint_from_stage(arguments['<stage>']),
        arguments['<api_token>'],
        arguments['<framework_slug>'],
    )
