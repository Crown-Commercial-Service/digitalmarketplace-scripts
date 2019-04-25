#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
!!! This generally needs to be run right after the close of applications for a framework, and passed to product
!!! managers & CCS.

Generate a CSV with per-lot draft statistics for each supplier who registered interest in the framework,
whether or not they made a complete application in the end.

Fields included:
* Supplier ID
* Supplier DM name
* Application / no_application
* The status of their declaration
* The number of services submitted and left in draft per lot

Usage:
    scripts/generate-framework-master-csv.py <framework_slug> <stage> <auth_token> <output-dir> [--excluded-supplier-ids=<excluded_supplier_ids>]

Example:
    scripts/generate-framework-master-csv.py g-cloud-11 preview myToken path/to/myfolder --excluded-supplier-ids=123,456,789
"""
import os
import sys
from datetime import datetime

from dmapiclient import DataAPIClient
from docopt import docopt
sys.path.insert(0, '.')

from dmscripts.generate_framework_master_csv import GenerateMasterCSV
from dmutils.env_helpers import get_api_endpoint_from_stage

if __name__ == "__main__":
    arguments = docopt(__doc__)

    output_dir = arguments['<output-dir>']
    stage = arguments['<stage>']
    framework_slug = arguments['<framework_slug>']
    filename = "{}-application-export-{}-{}.csv".format(
        framework_slug,
        stage,
        datetime.utcnow().strftime("%Y-%m-%d_%H.%M-")
    )

    # Create output directory if it doesn't already exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=arguments['<auth_token>'],
    )
    csv_builder = GenerateMasterCSV(
        client=client,
        target_framework_slug=framework_slug
    )

    if arguments.get('<excluded_supplier_ids>', False):  # updates the generator with any IDs the user wants excluded
        csv_builder.excluded_supplier_ids = [int(n) for n in arguments['<excluded_supplier_ids>'].split(',')]
    
    csv_builder.populate_output()

    with open(os.path.join(output_dir, filename), 'w') as csvfile:
        csv_builder.write_csv(outfile=csvfile)
