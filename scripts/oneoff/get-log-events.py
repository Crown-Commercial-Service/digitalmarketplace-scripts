#!/usr/bin/env python
"""
This script will write to the declared directory all log files of the chosen arn/group/stream.

You must be connected to the VPN and use an AWS_PROFILE and arn with access to AWS cloudwatch.

Usage:
    ./scripts/oneoff/get-log-events.py [options] <arn> <group> <stream> <directory>

Example:
    ./scripts/oneoff/get-log-events.py \\
        "arn:aws:iam::161120766136:role/RoleName" \\
        "prod-group-name" \\
        "9e1b2784-39cc-5016-87c0-845e" \\
        "/local/directory>"

Options:
    <arn>       An ARN matching the AWS_PROFILE used and has access to the get_log_events endpoint of CloudWatch.
    <group>     The name of the log group that contains the stream desired.
    <stream>    The name of the log stream from which log events will be retrieved.
    <directory> Absolute path to the directory where the log events will be written.
    -h, --help  Show this screen.
"""
from docopt import docopt
import sys
sys.path.insert(0, '.')

from dmscripts.get_log_events import LogRetriever

if __name__ == '__main__':
    doc_opt_arguments = docopt(__doc__)
    lr = LogRetriever(
        doc_opt_arguments['<arn>'],
        doc_opt_arguments['<group>']
    )
    sys.exit(
        lr.get_log_events(
            doc_opt_arguments['<stream>'],
            doc_opt_arguments['<directory>']
        )
    )
