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

from pathlib import Path
import csv
import sys

from docopt import docopt

from dmcontent.content_loader import ContentLoader

sys.path.insert(0, '.')
from dmscripts.helpers.search_filters import filters_for_lot


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


if __name__ == "__main__":
    main()
