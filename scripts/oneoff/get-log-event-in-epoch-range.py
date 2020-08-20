#!/usr/bin/env python
"""
This script will write to the declared directory all log files
of the chosen arn/group of streams within the defined interval.

The interval's timezone is the same as AWS region's timezone.

You must be connected to the VPN and use an AWS_PROFILE and arn with access to AWS cloudwatch.

Usage:
    ./scripts/oneoff/get-log-event-in-epoch-range.py [options] <arn> <group> <directory> <earliest> <latest>

Example:
    ./scripts/oneoff/get-log-event-in-epoch-range.py \\
        "arn:aws:iam::161120766136:role/RoleName" \\
        "prod-group-name" \\
        "/local/directory>" \\
        "2020-07-20 00:00:00" \\
        "2020-07-20 23:59:59"

Options:
    <arn>       An ARN matching the AWS_PROFILE used and has access to the get_log_events endpoint of CloudWatch.
    <group>     The name of the log group that contains the stream desired.
    <directory> Absolute path to the directory where the log events will be written.
    <earliest>  The earliest date before which streams will be excluded. Must follow the format '%Y-%m-%d %H:%M:%S'.
    <latest>    The latest date after which streams will be excluded. Must follow the format '%Y-%m-%d %H:%M:%S'.
    -h, --help  Show this screen.
"""
from docopt import docopt
import sys
sys.path.insert(0, '.')

from datetime import datetime
from dmscripts.get_log_events import LogRetriever

if __name__ == '__main__':
    doc_opt_arguments = docopt(__doc__)
    lr = LogRetriever(
        doc_opt_arguments['<arn>'],
        doc_opt_arguments['<group>']
    )
    sys.exit(
        lr.get_log_event_in_epoch_range(
            doc_opt_arguments['<directory>'],
            int(datetime.strptime(doc_opt_arguments['<earliest>'], '%Y-%m-%d %H:%M:%S').timestamp()),
            int(datetime.strptime(doc_opt_arguments['<latest>'], '%Y-%m-%d %H:%M:%S').timestamp())
        )
    )
