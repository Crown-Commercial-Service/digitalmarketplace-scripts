#!/usr/bin/env python3

"""
List a spreadsheet with all search filter types and options for a framework

To be able to analyse the way users can search for services and opportunities
it is useful to be able to see all the different filter options available from
a top-level view. Unfortunately the actual content is spread around several
different files in the frameworks repo, so this script stitches it all together
into one spreadsheet.

Usage:
    ./scripts/oneoff/export-framework-search-filters.py [options] <framework_slug>

Options:
    --frameworks-repo=<path>  Path to digitalmarketplace-frameworks [default: ../digitalmarketplace-frameworks]

Example:
    ./scripts/oneoff/export-framework-search-filters.py g-cloud-12 > g-cloud-12-filters.csv

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

from docopt import docopt

from dmcontent.content_loader import ContentLoader, ContentManifest


def main():
    args = docopt(__doc__)

    frameworks_repo = Path(args["--frameworks-repo"]).resolve()
    framework_slug = args["<framework_slug>"]

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

    writer.writerow(["lot", "filter name", "filter value", "filter sub-value"])

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

    # start with filters that are common to all lots
    common_filters = filters_for_lot("all", manifest, framework_lots)
    writer.writerow(["Any lot", "", ""])
    writer.writerows(rows_for_filters(common_filters))

    for lot in framework_lots:
        writer.writerow([lot.get("name", lot["slug"])])
        writer.writerows(rows_for_filters(filters_for_lot(lot["slug"], manifest, framework_lots)))


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
