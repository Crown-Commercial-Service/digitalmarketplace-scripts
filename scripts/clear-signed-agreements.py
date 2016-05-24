#!/usr/bin/env python
"""Remove all uploaded signed agreements and supplier agreementReturned flags for framework

Should be used if the new framework agreement document has been uploaded and all previously
signed agreements are no longer valid.

Since there's no way to check that the uploaded signed agreement document matches the latest
framework agreement version some of the agreements uploaded after the cleanup might still be
outdated (eg if a supplier downloaded the agreement file days ago).

This should be run before the new agreements are uploaded: this way there's no risk of removing
new agreements signed by the suppliers.

Usage:
    scripts/oneoff/clear-signed-agreements.py <stage> <framework_slug> --api-token=<api_access_token>
        [--supplier_ids=<supplier_ids>]

Options:
    --api-token=<api_access_token>  API token
    --supplier_ids=<supplier_ids>   Suppliers to target (comma-separated)

"""
import sys
sys.path.insert(0, '.')

import re
import getpass
import csv

from docopt import docopt

from dmutils.s3 import S3
from dmapiclient import DataAPIClient
from dmscripts import logging
from dmscripts.env import get_api_endpoint_from_stage

logger = logging.configure_logger()


def main(stage, framework_slug, api_token, user, supplier_ids=None):
    agreements_bucket_name = 'digitalmarketplace-agreements-{0}-{0}'.format(stage)
    agreements_bucket = S3(agreements_bucket_name)

    api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage, 'api'),
        api_token
    )

    suppliers = api_client.find_framework_suppliers(framework_slug, agreement_returned=True)['supplierFrameworks']

    if supplier_ids is not None:
        supplier_ids = validate_entered_ids(supplier_ids, suppliers)
    else:
        supplier_ids = [supplier['supplierId'] for supplier in suppliers]

    for supplier_id in supplier_ids:
        logger.info("Resetting agreement returned flag for supplier {supplier_id}",
                    extra={'supplier_id': supplier_id})
        api_client.unset_framework_agreement_returned(supplier_id, framework_slug, user)

    signed_agreements = filter(
        lambda x: match_signed_agreements(supplier_ids, x['path']),
        agreements_bucket.list('{}/agreements/'.format(framework_slug))
    )

    for document in signed_agreements:
        logger.info("Deleting {path}", extra={'path': document['path']})
        agreements_bucket.delete_key(document['path'])


def validate_entered_ids(entered_ids, suppliers):
    def match_format(id):
        match = re.match('^\d+$', id)
        if match:
            return True
        else:
            sys.exit("{} is the wrong format for a supplier id".format(id))

    def match_supplier(id):
        supplier = filter(
            lambda x: x['supplierId'] == int(id),
            suppliers
        )
        if supplier:
            return True
        else:
            sys.exit("{} is not a valid supplier who has signed the agreement".format(id))
            return False

    return [int(id) for id in entered_ids.split(',') if match_format(id) and match_supplier(id)]


def match_signed_agreements(supplier_ids, path):
    match = re.search(r'/(\d+)-signed-framework-agreement', path)
    return match and int(match.group(1)) in supplier_ids


if __name__ == '__main__':
    arguments = docopt(__doc__)
    stage = arguments['<stage>']
    framework_slug = arguments['<framework_slug>']
    data_api_access_token = arguments['--api-token']
    supplier_ids = arguments['--supplier_ids']

    user = getpass.getuser()

    main(stage, framework_slug, data_api_access_token, user, supplier_ids)
