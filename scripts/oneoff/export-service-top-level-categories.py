#!/usr/bin/env python3

"""
List a spreadsheet with services and their associated top-level filter categories
Note this only works for cloud-software lot as this is the only lot with sub-filter categories which are grouped

Usage:
    ./scripts/oneoff/export-service-top-level-categories.py [options] <framework_slug> <lot> <stage>

Options:
    --frameworks-repo=<path>  Path to digitalmarketplace-frameworks [default: ../digitalmarketplace-frameworks]

Example: ./scripts/oneoff/export-service-top-level-categories.py g-cloud-11 cloud-software preview >
g-cloud-11-cloud-software-top-level-categories.csv


BUGS:

- This code currently only works for G-Cloud
- There is a large amount of code copied and pasted from the buyer frontend,
  ideally it would be included some other way
"""

from pathlib import Path
import csv
import sys
from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage

from docopt import docopt

from dmcontent.content_loader import ContentLoader

sys.path.insert(0, '.')
from dmscripts.helpers.search_filters import filters_for_lot
from dmscripts.helpers.auth_helpers import get_auth_token


def main():
    args = docopt(__doc__)

    frameworks_repo = Path(args["--frameworks-repo"]).resolve()
    framework_slug = args["<framework_slug>"]
    stage = args["<stage>"]
    lot = args["<lot>"]

    data_api_client = DataAPIClient(get_api_endpoint_from_stage(stage), get_auth_token('api', stage))

    content_loader = ContentLoader(frameworks_repo)
    content_loader.load_manifest(framework_slug, "services", "services_search_filters")
    manifest = content_loader.get_manifest(framework_slug, "services_search_filters")

    # FIXME there isn't a uniform way to get the lots from the framework
    # content repo, hard code for G-Cloud for now
    framework_lots = [
        {"name": "Cloud hosting", "slug": "cloud-hosting"},
        {"name": "Cloud software", "slug": "cloud-software"},
        {"name": "Cloud support", "slug": "cloud-support"},
    ]

    writer = csv.writer(sys.stdout)

    # do the thing
    writer.writerow(['serviceId', 'topLevelCategories'])
    for service in data_api_client.find_services_iter(framework=framework_slug, status='published', lot=lot):
        service_categories = service['serviceCategories'] if service.get('serviceCategories') else []

        top_level_categories = []

        for f in filters_for_lot(service['lot'], manifest, framework_lots)['categories']['filters']:
            children = [f['label'] for f in f['children']] if f.get('children') else []
            if any(item in service_categories for item in children):
                top_level_categories.append(f['label'])

        writer.writerow([service['id'], '; '.join(top_level_categories)])


if __name__ == "__main__":
    main()
