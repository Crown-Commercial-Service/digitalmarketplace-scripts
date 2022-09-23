#!/usr/bin/env python3
"""

For a G-Cloud framework, this will export information about the bueyr activitites on the framework

Usage:
    scripts/export-g-cloud-user-data.py <stage> <framework_slug> [options]

Options:
    -v --verbose                Print INFO level messages.
    --output-dir=<output_dir>   Directory to write csv files to [default: data]
"""

from urllib.parse import urlparse, parse_qs
import datetime
import os
import sys

sys.path.insert(0, '.')

import logging
from docopt import docopt

from dmapiclient import DataAPIClient
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage

from dmscripts.helpers.csv_helpers import write_csv
from dmscripts.helpers import logging_helpers


def determine_next_framework_live_at(data_api_client, framework_slug):
    if framework_slug == 'g-cloud-12':
        return (datetime.datetime.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    else:
        next_framework = f'g-cloud-{int(framework_slug[8:]) + 1}'

        return data_api_client.get_framework(next_framework)['frameworks']['frameworkLiveAtUTC']


def determine_lot(search_url):
    parsed_url = urlparse(search_url)
    query_params = parse_qs(parsed_url.query)

    if 'filter_lot' in query_params:
        return query_params['filter_lot'][0].replace('-', '_')
    else:
        return 'all_lots'


def determine_project_type(project):
    if project['lockedAt'] is not None:
        if project['outcome'] is not None:
            if 'awarded' in project['outcome']:
                return 'awarded'
            elif project['outcome']['completed'] == 'cancelled':
                return 'cancelled'
            else:
                return 'none_suitable'
        else:
            return 'exported_results'
    else:
        return 'searches'


class ProgressBar:
    def __init__(self, max_bars, total_count) -> None:
        self._max_bars = max_bars
        self._total_count = total_count
        self._max_number_of_digits = len(str(total_count))

    def get_progreess_bar(self, count) -> str:
        number_of_bars = int(self._max_bars * count / self._total_count)
        number_of_blanks = self._max_bars - number_of_bars

        return f"{count:{self._max_number_of_digits}}/{self._total_count} " \
               f"[{'-' * number_of_bars}{' ' * number_of_blanks}]"


MAX_BARS = 50
DESIRED_KEYS = [
    'email_address',
    'total_projects',
    'cloud_hosting',
    'cloud_software',
    'cloud_support',
    'all_lots',
    'searches',
    'exported_results',
    'awarded',
    'cancelled',
    'none_suitable'
]


if __name__ == '__main__':
    arguments = docopt(__doc__)

    STAGE = arguments['<stage>']
    FRAMEWORK_SLUG = arguments['<framework_slug>']
    OUTPUT_DIR = arguments['--output-dir']
    VERBOSE = arguments['--verbose']

    if not FRAMEWORK_SLUG.startswith('g-cloud'):
        print(f'Not a G-Cloud framework `{FRAMEWORK_SLUG}`')
        exit(1)

    logger = logging_helpers.configure_logger(
        {"dmapiclient": logging.INFO} if VERBOSE else {"dmapiclient": logging.WARN}
    )

    if not os.path.exists(OUTPUT_DIR):
        logger.info("Creating {} directory".format(OUTPUT_DIR))
        os.makedirs(OUTPUT_DIR)

    client = DataAPIClient(get_api_endpoint_from_stage(STAGE), get_auth_token('api', STAGE))

    framework_live_at = client.get_framework(FRAMEWORK_SLUG)['frameworks']['frameworkLiveAtUTC']
    next_framework_live_at = determine_next_framework_live_at(client, FRAMEWORK_SLUG)

    direct_award_projects = {}

    print(f'Getting users and direct award projects for {FRAMEWORK_SLUG}')

    for direct_award_project in client.find_direct_award_projects_iter(latest_first=True, with_users=True):
        if direct_award_project['createdAt'] >= next_framework_live_at:
            continue
        elif direct_award_project['createdAt'] < framework_live_at:
            break
        else:
            user = direct_award_project['users'][0]
            user_id = user['id']
            user_email = user['emailAddress']

            if user_id not in direct_award_projects:
                direct_award_projects[user_id] = {
                    'email_address': user_email,
                    'project_ids': [],
                    'total_projects': 0,
                    'cloud_hosting': 0,
                    'cloud_software': 0,
                    'cloud_support': 0,
                    'all_lots': 0,
                    'searches': 0,
                    'exported_results': 0,
                    'awarded': 0,
                    'cancelled': 0,
                    'none_suitable': 0
                }

            direct_award_projects[user_id]['project_ids'].append(direct_award_project['id'])

    total_count = len(direct_award_projects)

    print(f'Found {total_count} users with {FRAMEWORK_SLUG} projects')

    count = 0

    progess_bar = ProgressBar(MAX_BARS, total_count)

    for user_id in direct_award_projects:
        count += 1
        print(f'Getting the info for the projects: {progess_bar.get_progreess_bar(count)}', end='\r')

        direct_award_project = direct_award_projects[user_id]

        direct_award_project['total_projects'] = len(direct_award_project['project_ids'])

        for project_id in direct_award_project['project_ids']:
            project_search = [
                search for search in client.find_direct_award_project_searches_iter(project_id) if search['active']
            ][0]

            lot = determine_lot(project_search['searchUrl'])

            direct_award_project[lot] += 1

            project_type = determine_project_type(client.get_direct_award_project(project_id)['project'])

            direct_award_project[project_type] += 1

    print(f'Getting the info for the projects: {progess_bar.get_progreess_bar(count)}')
    print('Formatting the users data')

    formated_data = []

    for user_id in direct_award_projects:
        direct_award_project = direct_award_projects[user_id]

        formated_data_item = {
            desired_key: direct_award_project[desired_key] for desired_key in DESIRED_KEYS
        }

        formated_data_item['user_id'] = user_id

        formated_data.append(formated_data_item)

    print('Exporting the users data')

    write_csv(
        ['user_id'] + DESIRED_KEYS,
        formated_data,
        os.path.join(OUTPUT_DIR, f"g-cloud-user-data-{STAGE}.csv")
    )
