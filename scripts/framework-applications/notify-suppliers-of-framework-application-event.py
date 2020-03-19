#!/usr/bin/env python3
"""
Notify all users of all suppliers that have any interest in the framework identified by <framework_slug> about a
framework event, for example new publication of clarification questions, or an approaching deadline.

For all emails, the Notify email context includes:
- framework_name            e.g. G-Cloud 12
- updates_url               e.g. https://www.digitalmarketplace.service.gov.uk/suppliers/frameworks/g-cloud-12/updates
- framework_dashboard_url   e.g. https://www.digitalmarketplace.service.gov.uk/suppliers/frameworks/g-cloud-12/
- clarification_questions_closed ('yes' or 'no')
- framework date strings in various formats ('timetoday' is only available if script is triggered on that datestamp
    and the time is hour-exact, e.g. 5pm):

    clarificationsCloseAt_displaytimeformat: '5:00pm BST'
    clarificationsCloseAt_dateformat: 'Saturday 1 January 2000'
    clarificationsCloseAt_datetimeformat: 'Saturday 1 January 2000 at 5:00pm BST'

    clarificationsPublishAt_displaytimeformat: '5:00pm BST'
    clarificationsPublishAt_dateformat: 'Sunday 2 January 2000'
    clarificationsPublishAt_datetimeformat: 'Sunday 2 January 2000 at 5:00pm BST'
    clarificationsPublishAt_timetoday: 'Today at 5pm BST' (only available if script is triggered on that datestamp)

    applicationsCloseAt_displaytimeformat: '12:00am GMT'
    applicationsCloseAt_dateformat: 'Monday 3 January 2000'
    applicationsCloseAt_datetimeformat: 'Monday 3 January 2000 at 12:00am GMT'
    applicationsCloseAt_timetoday: 'Today at 5pm BST' (only available if script is triggered on that datestamp)

    intentionToAwardAt_displaytimeformat: '5:00pm BST'
    intentionToAwardAt_dateformat: 'Thursday 29 June 2000'
    intentionToAwardAt_datetimeformat: 'Thursday 29 June 2000 at 5:00pm BST'
    intentionToAwardAt_timetoday: 'Today at 5pm BST' (only available if script is triggered on that datestamp)

    frameworkLiveAt_displaytimeformat: '5:30pm BST'
    frameworkLiveAt_dateformat: 'Thursday 29 June 2000'
    frameworkLiveAt_datetimeformat: 'Thursday 29 June 2000 at 5:30pm BST'

    frameworkExpiresAt_displaytimeformat: '12:00am GMT'
    frameworkExpiresAt_dateformat: 'Thursday 6 January 2000'
    frameworkExpiresAt_datetimeformat: 'Thursday 6 January 2000 at 12:00am GMT'

Usage: notify-suppliers-of-framework-application-event.py <stage> <framework_slug> <govuk_notify_api_key>
    <govuk_notify_template_id> [--dry-run] [--resume-run-id=<run_id>]

Options:
    --stage=<stage>                                       Stage to target
    --govuk_notify_api_key=<govuk_notify_api_key>         Notify API Token
    --govuk_notify_template_id=<govuk_notify_template_id> Notify template id on account corresponding to token provided
    --resume-run-id=<run_id>                              UUID of a previously failed run to use for notify ref
                                                          generation: useful to prevent emails being re-sent to those
                                                          users the previous run was already successful for
    --dry-run                                             List notifications that would be sent without sending emails
    -h, --help                                            Show this screen

Examples:
    ./scripts/framework-applications/notify-suppliers-of-framework-application-event.py \
        preview g-cloud-99 notifyToken t3mp1at3id

    ./scripts/framework-applications/notify-suppliers-of-framework-application-event.py \
        preview g-cloud-99 notifyToken t3mp1at3id \
        --dry-run --verbose --resume-run-id=00010203-0405-0607-0809-0a0b0c0d0e0f

"""

import logging
import sys
from uuid import UUID

from docopt import docopt

from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage

sys.path.insert(0, '.')
from dmscripts.helpers.email_helpers import scripts_notify_client
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers import logging_helpers
from dmscripts.notify_suppliers_of_framework_application_event import \
    notify_suppliers_of_framework_application_event


if __name__ == "__main__":
    arguments = docopt(__doc__)

    logger = logging_helpers.configure_logger({"dmapiclient": logging.INFO})

    run_id = None if not arguments.get("<run_id>") else UUID(arguments["<run_id>"])

    failure_count = notify_suppliers_of_framework_application_event(
        data_api_client=DataAPIClient(
            base_url=get_api_endpoint_from_stage(arguments["<stage>"], "api"),
            auth_token=get_auth_token("api", arguments["<stage>"]),
        ),
        notify_client=scripts_notify_client(arguments['<govuk_notify_api_key>'], logger=logger),
        notify_template_id=arguments['<govuk_notify_template_id>'],
        framework_slug=arguments["<framework_slug>"],
        stage=arguments["<stage>"],
        dry_run=arguments["--dry-run"],
        logger=logger,
        run_id=run_id,
    )

    if failure_count:
        logger.error("Failed sending {failure_count} messages", extra={"failure_count": failure_count})

    sys.exit(failure_count)
