#!/usr/bin/env python
"""
This script will write to the declared directory all log files of the chosen arn/group/stream.

You must be connected to the VPN and use an arn with access to AWS cloudwatch.

Usage:
    ./scripts/oneoff/get-log-events.py [options] <arn> <group> <stream> <directory>

Example:
    ./scripts/oneoff/get-log-events.py "arn:aws:iam::x:role/RoleName" "prod-group-name" "x" "/Users/username/test"

Options:
    <arn>       arn:aws:iam::161120766136:role/RoleName
    <group>     prod-group-name
    <stream>    9e1b2784-39cc-5016-87c0-845e
    <directory> /Users/username/Downloads/test  # must be absolute
    -h, --help  Show this screen
"""
from docopt import docopt
import sys
sys.path.insert(0, '.')

from dmscripts.get_log_events import get_log_events

if __name__ == '__main__':
    doc_opt_arguments = docopt(__doc__)
    sys.exit(
        get_log_events(
            doc_opt_arguments['<arn>'],
            doc_opt_arguments['<group>'],
            doc_opt_arguments['<stream>'],
            doc_opt_arguments['<directory>']
        )
    )
