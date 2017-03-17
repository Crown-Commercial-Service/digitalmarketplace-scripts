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


if __name__ == "__main__":
    arguments = docopt(__doc__)
    ok = main(
        mailchimp_username=arguments['--mailchimp-username'],
        mailchimp_api_key=arguments['--mailchimp-api-key']
    )

    if not ok:
        sys.exit(1)
