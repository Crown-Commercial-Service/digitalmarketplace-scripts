#!/usr/bin/env python
"""
If a brief has been withdrawn suppliers need to be notified that their applications have also been cancelled. This
script notifies suppliers of all briefs withdrawn on a given date. Alternatively, when supplied with a given brief id
it will notify just the suppliers with responses to that brief (requires brief withdrawal date).

Usage: notify-suppliers-of-brief-withdrawl.py <stage> <govuk_notify_api_key>
    <govuk_notify_template_id> [<withdrawn_date>] [<brief_id>] [--dry-run] [--verbose]

Options:
    --stage=<stage>                                       Stage to target
    --govuk_notify_api_key=<govuk_notify_api_key>         Notify API Token
    --govuk_notify_template_id=<govuk_notify_template_id> Notify template id on account corresponding to token provided
    --withdrawn_date=[<withdrawn_date>]                   Notify users of briefs withdrawn on this date, defaults to
                                                              # yesterday (date format: YYYY-MM-DD)
    --brief_id=[<brief_id>]                               Only notify suppliers for this brief. Requires withdrawn_date.
    --dry-run                                             List notifications that would be sent without sending emails
    --verbose
    -h, --help                                            Show this screen

Examples:
    ./scripts/notify-suppliers-of-brief-withdrawal.py preview myToken notifyToken t3mp1at3id 2017-10-27
    ./scripts/notify-suppliers-of-brief-withdrawal.py preview myToken notifyToken t3mp1at3id --dry-run --verbose

"""

import logging
import sys
from datetime import datetime, timedelta
from docopt import docopt

from dmutils.formats import DATE_FORMAT
from dmapiclient import DataAPIClient

sys.path.insert(0, '.')

from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmscripts.notify_suppliers_of_brief_withdrawal import main


if __name__ == "__main__":
    arguments = docopt(__doc__)

    # Get arguments
    stage = arguments['<stage>']
    govuk_notify_api_key = arguments['<govuk_notify_api_key>']
    govuk_notify_template_id = arguments['<govuk_notify_template_id>']
    withdrawn_date = arguments.get('<withdrawn_date>', None)
    brief_id = int(arguments.get('<brief_id>')) if arguments.get('<brief_id>', None) else None
    dry_run = arguments['--dry-run']
    verbose = arguments['--verbose']

    # Set defaults, instantiate clients
    logger = logging_helpers.configure_logger(
        {"dmapiclient": logging.INFO} if verbose else {"dmapiclient": logging.WARN}
    )
    withdrawn_date = (
        withdrawn_date and datetime.strptime(withdrawn_date, DATE_FORMAT).date() or
        datetime.today().date() - timedelta(days=1)
    )
    notify_client = scripts_notify_client(govuk_notify_api_key, logger=logger)
    data_api_client = DataAPIClient(base_url=get_api_endpoint_from_stage(stage),
                                    auth_token=get_auth_token('api', stage))

    # Do send
    ok = main(
        data_api_client=data_api_client,
        mail_client=notify_client,
        template_id=govuk_notify_template_id,
        stage=stage,
        logger=logger,
        withdrawn_date=withdrawn_date,
        brief_id=brief_id,
        dry_run=dry_run,
    )

    if not ok:
        sys.exit(1)
