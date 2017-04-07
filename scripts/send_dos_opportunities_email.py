#!/usr/bin/env python

"""Description to be added here

Usage:
    send_dos_opportunities_email.py --mailchimp-username=<mailchimp_username>
                                             --mailchimp-api-key=<mailchimp_api_key>
"""

import sys

from docopt import docopt

sys.path.insert(0, '.')
from dmscripts.send_dos_opportunities_email import main

lots = [
    {
        "lot_slug": "digital-specialists",
        "lot_name": "Digital specialists",
        "list_id": "096e52cebb"
    },
    {
        "lot_slug": "digital-outcomes",
        "lot_name": "Digital outcomes",
        "list_id": "096e52cebb"
    },
    {
        "lot_slug": "user-research-participants",
        "lot_name": "User research participants",
        "list_id": "096e52cebb"
    }
]

if __name__ == "__main__":
    arguments = docopt(__doc__)
    lots = ['ds', 'do', 'urp']
    for lot in lots:
        ok = main(
            mailchimp_username=arguments['--mailchimp-username'],
            mailchimp_api_key=arguments['--mailchimp-api-key'],
            lot=lot
        )

    if not ok:
        sys.exit(1)
