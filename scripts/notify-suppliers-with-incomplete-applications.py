#!/usr/bin/env python
"""
Execute this script about a week before a framework closes to remind suppliers that have incomplete applications
of the looming deadline.

The script will notify suppliers that have:

1) unconfirmed company details
2) incomplete declarations
3) no completed services

Uses the Notify API to send emails.

Usage:
    scripts/notify-suppliers-with-incomplete-applications.py [options] <stage> <framework> <notify_api_key>

Example:
    scripts/notify-suppliers-with-incomplete-applications.py --dry-run preview g-cloud-9 my-awesome-key

Options:
    <stage>                     Environment to run script against.
    <framework>                 Framework slug.
    <notify_api_key>            API key for GOV.UK Notify.

    -n, --dry-run               Run script without sending emails.

    -h, --help                  Show this screen
"""
from docopt import docopt
import sys
sys.path.insert(0, '.')
from dmscripts.notify_suppliers_with_incomplete_applications import notify_suppliers_with_incomplete_applications


if __name__ == '__main__':
    doc_opt_arguments = docopt(__doc__)
    sys.exit(
        notify_suppliers_with_incomplete_applications(
            doc_opt_arguments['<framework>'],
            doc_opt_arguments['<stage>'],
            doc_opt_arguments['<notify_api_key>'],
            doc_opt_arguments['--dry-run']
        )
    )
