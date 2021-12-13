#!/usr/bin/env python3
"""
For performance testing, we need suppliers who are able to copy services from the previous iteration of the framework.
Get up to 1000 suitable suppliers and then remove their data for the new framework so they're in a clean state for use
in tests.
Usage:
    scripts/find-active-suppliers-since-a-date.py <stage> [options]
Options:
    --date=YYYY-MM-DD       Limit the number of suppliers to find [default: <today's date>]
"""
import sys

from os import environ
from dmapiclient import DataAPIClient
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt
from datetime import datetime

data_api_client = DataAPIClient(get_api_endpoint_from_stage(environ["STAGE"].lower()), get_auth_token("api", environ["STAGE"].lower()))

og_stdout = sys.stdout
counter = 0

arguments = docopt(__doc__)
date_format = "%Y-%m-%d"
usr_date = datetime.strptime(arguments['--date'], date_format) or datetime.now().strftime(date_format)

with open('suppliers_registered_%s.txt' % datetime.now().strftime("%H:%M:%S"), 'w') as f:
	sys.stdout = f
	for d in data_api_client.find_users_iter(role='supplier'):
		if d['active'] == True and datetime.strptime(d['createdAt'].split('T',1)[0], date_format) >= datetime.strptime(usr_date, date_format):
			print(d)
			counter += 1
 
	print("\nTotal Records Count:")
	print(counter)

sys.stdout = og_stdout
