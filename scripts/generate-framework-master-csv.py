#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
!!! This generally needs to be run right after the close of applications for a framework, and passed to product
!!! managers & CCS.

Generate a CSV (to stdout) with per-lot draft statistics for each supplier who registered interest in the framework,
whether or not they made a complete application in the end.

Fields included:
* Supplier ID
* Supplier DM name
* Application / no_application
* The status of their declaration
* The number of services submitted and left in draft per lot

Usage:
    scripts/generate-framework-master-csv.py <framework_slug> <stage> <auth_token>

Example:
    scripts/generate-framework-master-csv.py g-cloud-8 preview myToken | tee g-cloud-8-master.csv
"""
import sys

from dmapiclient import DataAPIClient
from docopt import docopt
sys.path.insert(0, '.')

from dmscripts.generate_framework_master_csv import GenerateMasterCSV
from dmscripts.helpers.env_helpers import get_api_endpoint_from_stage

if __name__ == "__main__":
    arguments = docopt(__doc__)

    client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(arguments['<stage>']),
        auth_token=arguments['<auth_token>'],
    )
    csv_builder = GenerateMasterCSV(
        client=client,
        target_framework_slug=arguments['<framework_slug>']
    )
    csv_builder.populate_output()
    csv_builder.write_csv()
