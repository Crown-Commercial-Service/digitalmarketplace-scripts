#!/usr/bin/env python3
"""
If a brief has been awarded suppliers need to be notified. This
script notifies suppliers of all awarded briefs in the previous day by default.
Alternatively, when supplied with a list of BriefResponse IDs, it will notify just the suppliers for those responses.

Usage:
    notify-suppliers-of-awarded-briefs.py <stage> <govuk_notify_api_key> <govuk_notify_template_id>
        [options]

Options:
    -h, --help                                      Display this screen
    -v, --verbose                                   Verbosity level
    --dry-run                                       Log without sending emails
    --awarded_at=<awarded_at>                       Notify applicants to briefs awarded on this date, defaults to
                                                    # yesterday (date format: YYYY-MM-DD)
    --brief_response_ids=<brief_response_ids>       List of brief response IDs to send to (for resending failures)

Examples:
    ./scripts/notify-suppliers-of-awarded-briefs.py preview myToken notifyToken t3mp1at3id --awarded_at=2017-10-27
    ./scripts/notify-suppliers-of-awarded-briefs.py preview myToken notifyToken t3mp1at3id --dry-run --verbose

"""

import logging
import sys
from docopt import docopt

from dmapiclient import DataAPIClient

sys.path.insert(0, '.')

from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmscripts.notify_suppliers_of_awarded_briefs import main
from dmutils.env_helpers import get_api_endpoint_from_stage


if __name__ == "__main__":
    arguments = docopt(__doc__)

    # Get arguments
    stage = arguments['<stage>']
    govuk_notify_api_key = arguments['<govuk_notify_api_key>']
    govuk_notify_template_id = arguments['<govuk_notify_template_id>']
    awarded_at = arguments.get('--awarded_at', None)
    brief_response_ids = arguments.get('--brief_response_ids', None)
    dry_run = arguments['--dry-run']
    verbose = arguments['--verbose']

    # Set defaults, instantiate clients
    logger = logging_helpers.configure_logger(
        {"dmapiclient": logging.INFO} if verbose else {"dmapiclient": logging.WARN}
    )
    notify_client = scripts_notify_client(govuk_notify_api_key, logger=logger)
    data_api_client = DataAPIClient(base_url=get_api_endpoint_from_stage(stage),
                                    auth_token=get_auth_token('api', stage))

    list_of_brief_response_ids = list(map(int, brief_response_ids.split(','))) if brief_response_ids else None

    # Do send
    ok = main(
        data_api_client=data_api_client,
        mail_client=notify_client,
        template_id=govuk_notify_template_id,
        stage=stage,
        logger=logger,
        awarded_at=awarded_at,
        brief_response_ids=list_of_brief_response_ids,
        dry_run=dry_run,
    )

    if not ok:
        sys.exit(1)
