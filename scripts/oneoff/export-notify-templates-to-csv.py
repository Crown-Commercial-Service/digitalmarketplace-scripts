#!/usr/bin/env python

"""
Script to fetch templates from the Notify API and export them to CSV.
See Notify's documentation: https://docs.notifications.service.gov.uk/python.html#get-all-templates

Usage:
    export-notify-templates-to-csv.py <notify_api_key> [options]

Options:
    --include-message-body      # Include multi-line message body field (makes the csv harder to read at-a-glance)
    --output-dir=<output_dir>   # Folder to output the CSV [default: output]

Example:
    export-notify-templates-to-csv.py myNotifyKey --output-dir=output --include-message-body
"""
import os
import sys
sys.path.insert(0, '.')

import csv
from docopt import docopt
from notifications_python_client import NotificationsAPIClient


NOTIFY_TEMPLATE_KEYS = [
    'id',
    'name',
    'subject',
    'type',
    'created_at',
    'created_by',
    'updated_at',
    'version',
    'personalisation',
    'body',
]


if __name__ == '__main__':
    arguments = docopt(__doc__)

    notify_api_key = arguments['<notify_api_key>']
    output_dir = arguments.get("--output-dir")
    include_message_body = arguments.get("--include-message-body")

    client = NotificationsAPIClient(notify_api_key)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # If we want to export the message body as well
    if include_message_body:
        headers = NOTIFY_TEMPLATE_KEYS
        filename = "notify-template-list-with-message-body.csv"
    else:
        headers = NOTIFY_TEMPLATE_KEYS[:-1]
        filename = "notify-template-list-without-message-body.csv"

    path = os.path.join(output_dir, filename)

    # Fetch templates
    resp = client.get_all_templates()

    with open(path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for template_json in resp['templates']:
            writer.writerow({key: value for key, value in template_json.items() if key in headers})
