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

from collections import OrderedDict
from pathlib import Path
from typing import List
import csv
import sys
from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage

from docopt import docopt

from dmcontent.content_loader import ContentLoader, ContentManifest

sys.path.insert(0, '.')
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


def rows_for_filters(filters: dict):
    for section in filters.values():
        yield ["", str(section["label"]), "", ""]
        for option in section["filters"]:
            yield ["", "", str(option["label"]), ""]
            # category filters can have sub-categories
            # (but not sub-sub-categories)
            if "children" in option:
                for suboption in option["children"]:
                    yield ["", "", "", suboption["label"]]

# the following functions were copied from the buyer frontend with minor alterations
# https://github.com/alphagov/digitalmarketplace-buyer-frontend/blob/a83163/app/main/presenters/search_presenters.py


def sections_for_lot(lot_slug: str, manifest: ContentManifest, all_lots: List[dict]):
    if lot_slug == 'all':
        for lot_slug in [x["slug"] for x in all_lots]:
            manifest = manifest.filter({'lot': lot_slug})
    else:
        manifest = manifest.filter({'lot': lot_slug})

    return manifest.sections


def filters_for_lot(lot_slug: str, manifest: ContentManifest, all_lots: List[dict]):
    sections = sections_for_lot(lot_slug, manifest, all_lots=all_lots)
    lot_filters: OrderedDict[str, dict] = OrderedDict()

    for section in sections:
        section_filter = {
            "label": section["name"],
            "slug": section["slug"],
            "filters": [],
        }
        for question in section["questions"]:
            section_filter["filters"].extend(
                filters_for_question(question)
            )

        lot_filters[section.slug] = section_filter

    return lot_filters


def filters_for_question(question):
    question_filters = []
    if question['type'] == 'boolean':
        question_filters.append({
            'label': question.get('filter_label') or question.get('name') or question['question'],
            'name': question['id'],
            'id': question['id'],
            'value': 'true',
        })

    elif question['type'] in ['checkboxes', 'radios', 'checkbox_tree']:
        _recursive_add_option_filters(question, question['options'], question_filters)

    return question_filters


def _recursive_add_option_filters(question, options_list, filters_list):
    for option in options_list:
        if not option.get('filter_ignore'):
            value = get_filter_value_from_question_option(option)
            presented_filter = {
                'label': option.get('filter_label') or option['label'],
                'name': question['id'],
                'id': '{}-{}'.format(
                    question['id'],
                    value.replace(' ', '-')),
                'value': value,
            }
            if option.get('options'):
                presented_filter['children'] = []
                _recursive_add_option_filters(question, option.get('options', []), presented_filter['children'])

            filters_list.append(presented_filter)


# the below functions were copied from buyer frontend, with modifications
# https://github.com/alphagov/digitalmarketplace-buyer-frontend/blob/a83163/app/main/helpers/search_helpers.py#L180

def get_filter_value_from_question_option(option):
    return option.get("value", option.get("label", ""))


if __name__ == "__main__":
    main()
