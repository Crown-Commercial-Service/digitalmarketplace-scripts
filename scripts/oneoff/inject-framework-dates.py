#!/usr/bin/env python3

"""
A one-off script for injecting dates from digitalmarketplace-frameworks/frameworks' `dates.yml` files into the API,
which is where we will store the canonical record of important lifecycle events from now on.

Syntax: ./scripts/oneoff/inject-framework-dates.py --stage preview
"""

import getpass
import sys

import argparse

sys.path.insert(0, '.')  # noqa

from dmapiclient import DataAPIClient
from dmscripts.helpers.auth_helpers import get_auth_token, get_api_url

# Dates taken from https://github.com/alphagov/digitalmarketplace-frameworks/blob
# /e1f8e5c4a1a98d817e1bc9ff90ace85c1a0762c6/frameworks/<framework>/messages/dates.yml
FRAMEWORKS_AND_DATES = {
    'digital-outcomes-and-specialists': {
        'clarificationsCloseAtUTC': '2016-01-06T17:00:00Z',
        'clarificationsPublishAtUTC': '2016-01-13T17:00:00Z',
        'applicationsCloseAtUTC': '2016-01-19T15:00:00Z',
        'intentionToAwardAtUTC': '2016-02-18T12:00:00Z',
        'frameworkLiveAtUTC': '2016-03-03T12:00:00Z',
        'frameworkExpiresAtUTC': '2017-01-27T12:00:00Z',
    },
    'digital-outcomes-and-specialists-2': {
        'clarificationsCloseAtUTC': '2016-12-01T17:00:00Z',
        'clarificationsPublishAtUTC': '2016-12-07T17:00:00Z',
        'applicationsCloseAtUTC': '2016-12-14T17:00:00Z',
        'intentionToAwardAtUTC': '2017-01-16T12:00:00Z',
        'frameworkLiveAtUTC': '2017-01-27T12:00:00Z',
        'frameworkExpiresAtUTC': '2018-01-29T12:00:00Z',
    },
    'digital-outcomes-and-specialists-3': {
        'clarificationsCloseAtUTC': '2525-01-01T12:00:00Z',
        'clarificationsPublishAtUTC': '2525-01-01T12:00:00Z',
        'applicationsCloseAtUTC': '2525-01-01T12:00:00Z',
        'intentionToAwardAtUTC': '2525-01-01T12:00:00Z',
        'frameworkLiveAtUTC': '2525-01-01T12:00:00Z',
        'frameworkExpiresAtUTC': '2525-01-01T12:00:00Z',
    },

    # Begin Unix epoch time polyfill.
    # We don't have dates for G-Cloud 4 to G-Cloud 6 in dm-frameworks, so set an obviously-wrong fallback.
    'g-cloud-4': {
        'clarificationsCloseAtUTC': '1970-01-01T00:00:00Z',
        'clarificationsPublishAtUTC': '1970-01-01T00:00:00Z',
        'applicationsCloseAtUTC': '1970-01-01T00:00:00Z',
        'intentionToAwardAtUTC': '1970-01-01T00:00:00Z',
        'frameworkLiveAtUTC': '1970-01-01T00:00:00Z',
        'frameworkExpiresAtUTC': '1970-01-01T00:00:00Z',
    },
    'g-cloud-5': {
        'clarificationsCloseAtUTC': '1970-01-01T00:00:00Z',
        'clarificationsPublishAtUTC': '1970-01-01T00:00:00Z',
        'applicationsCloseAtUTC': '1970-01-01T00:00:00Z',
        'intentionToAwardAtUTC': '1970-01-01T00:00:00Z',
        'frameworkLiveAtUTC': '1970-01-01T00:00:00Z',
        'frameworkExpiresAtUTC': '1970-01-01T00:00:00Z',
    },
    'g-cloud-6': {
        'clarificationsCloseAtUTC': '1970-01-01T00:00:00Z',
        'clarificationsPublishAtUTC': '1970-01-01T00:00:00Z',
        'applicationsCloseAtUTC': '1970-01-01T00:00:00Z',
        'intentionToAwardAtUTC': '1970-01-01T00:00:00Z',
        'frameworkLiveAtUTC': '1970-01-01T00:00:00Z',
        'frameworkExpiresAtUTC': '1970-01-01T00:00:00Z',
    },
    # End Unix epoch time polyfill.

    'g-cloud-7': {
        'clarificationsCloseAtUTC': '2015-09-22T17:00:00Z',
        'clarificationsPublishAtUTC': '2015-09-29T17:00:00Z',
        'applicationsCloseAtUTC': '2015-10-06T15:00:00Z',
        'intentionToAwardAtUTC': '2015-11-09T12:00:00Z',
        'frameworkLiveAtUTC': '2015-11-23T12:00:00Z',
        'frameworkExpiresAtUTC': '1970-01-01T00:00:00Z',
    },
    'g-cloud-8': {
        'clarificationsCloseAtUTC': '2016-07-07T16:00:00Z',
        'clarificationsPublishAtUTC': '2016-06-14T16:00:00Z',
        'applicationsCloseAtUTC': '2016-06-23T16:00:00Z',
        'intentionToAwardAtUTC': '2016-07-18T11:00:00Z',
        'frameworkLiveAtUTC': '2016-08-01T11:0:00Z',
        'frameworkExpiresAtUTC': '1970-01-01T00:00:00Z',
    },
    'g-cloud-9': {
        'clarificationsCloseAtUTC': '2017-03-28T16:00:00Z',
        'clarificationsPublishAtUTC': '2017-04-04T16:00:00Z',
        'applicationsCloseAtUTC': '2017-04-11T16:00:00Z',
        'intentionToAwardAtUTC': '2017-05-18T11:00:00Z',
        'frameworkLiveAtUTC': '2017-05-22T11:00:00Z',
        'frameworkExpiresAtUTC': '2018-05-21T11:00:00Z',
    },
    'g-cloud-10': {
        'clarificationsCloseAtUTC': '2018-05-09T16:00:00Z',
        'clarificationsPublishAtUTC': '2018-05-16T16:00:00Z',
        'applicationsCloseAtUTC': '2018-05-23T16:00:00Z',
        'intentionToAwardAtUTC': '2018-06-18T11:00:00Z',
        'frameworkLiveAtUTC': '2018-07-02T11:00:00Z',
        'frameworkExpiresAtUTC': '1970-01-01T00:00:00Z',
    }
}


def inject_framework_dates(stage):
    data_api_token = get_auth_token('api', stage) if stage != 'development' else 'myToken'
    data_api_client = DataAPIClient(get_api_url('api', stage), data_api_token)

    for framework_slug, framework_data in FRAMEWORKS_AND_DATES.items():
        print(f'Injecting dates for {framework_slug}: {framework_data}')
        try:
            data_api_client.update_framework(framework_slug=framework_slug,
                                             data=framework_data,
                                             user=f'{getpass.getuser()} - '
                                                  f'digitalmarketplace-scripts/scripts/'
                                                  f'oneoff/inject-framework-dates.py')

        except Exception as e:
            print(f'Failed with {e} on {framework_slug}. Data: {framework_data}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', default='development', choices=['development', 'preview', 'staging', 'production'],
                        help="Which stage's API to communicate with.")

    args = parser.parse_args()

    inject_framework_dates(stage=args.stage.lower())
