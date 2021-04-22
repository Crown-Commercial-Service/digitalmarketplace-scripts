#!/usr/bin/env python3
"""
If a brief has been awarded suppliers need to be notified. This script notifies
suppliers of all awarded briefs in the previous day by default.

Alternatively, when supplied with a list of BriefResponse IDs, it will notify
just the suppliers for those responses.
"""

__examples__ = r"""
Examples:
    ./scripts/notify-suppliers-of-awarded-briefs.py \
        --stage=preview --notify-api-key=notifyToken --notify-template-id=t3mp1at3id --awarded-at=2017-10-27
    ./scripts/notify-suppliers-of-awarded-briefs.py \
        --stage=preview --notify-api-key=notifyToken --notify-template-id=t3mp1at3id --dry-run --verbose
"""

import sys

sys.path.insert(0, ".")

from dmscripts.notify_suppliers_of_awarded_briefs import main
from dmscripts.email_engine import email_engine, argument_parser_factory


if __name__ == "__main__":
    arg_parser = argument_parser_factory(
        description=__doc__, epilog=__examples__, notify_template_id_required=True
    )

    # Get arguments
    arg_parser.add_argument(
        "--awarded-at",
        help="Notify applicants to briefs awarded on this date, defaults to yesterday (date format: YYYY-MM-DD).",
    )
    arg_parser.add_argument(
        "--brief-response-ids",
        help="Comma-seperated list of brief response IDs to send to.",
        type=lambda s: [int(i) for i in s.split(",")]
    )

    args = arg_parser.parse_args()

    # Do send
    email_engine(
        main,
        args=args,
    )
