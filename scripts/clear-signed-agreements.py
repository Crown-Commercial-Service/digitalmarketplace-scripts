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
    scripts/clear-signed-agreements.py <stage> <framework_slug> --api-token=<api_access_token>
    [<supplier_id_file>] [<cutoff_time>]

Arguments:
    <cutoff_time>  if set, the script will only remove agreements uploaded before the given timestamp.
                   This should be a valid ISO 8601 string (eg 2016-08-22T00:00:00.00000Z)

Options:
    --api-token=<api_access_token>  API token

"""
import sys
sys.path.insert(0, '.')

import re
import getpass

from docopt import docopt

from dmutils.s3 import S3
from dmapiclient import DataAPIClient
from dmscripts import logging
from dmscripts.env import get_api_endpoint_from_stage

logger = logging.configure_logger()


def main(stage, framework_slug, api_token, user, supplier_ids=None, cutoff_time=None):
    agreements_bucket_name = 'digitalmarketplace-agreements-{0}-{0}'.format(stage)
    agreements_bucket = S3(agreements_bucket_name)

    api_client = DataAPIClient(
        get_api_endpoint_from_stage(stage, 'api'),
        api_token
    )

    suppliers = api_client.find_framework_suppliers(framework_slug, agreement_returned=True)['supplierFrameworks']

    if supplier_ids is not None:
        suppliers = [
            supplier for supplier in suppliers
            if supplier['supplierId'] in supplier_ids
            and (not cutoff_time or supplier['agreementReturnedAt'] < cutoff_time)
        ]
        supplier_ids = [supplier['supplierId'] for supplier in suppliers]

    for supplier in suppliers:
        logger.info("Resetting agreement returned flag for supplier {supplier_id} returned at {returned_at}",
                    extra={'supplier_id': supplier['supplierId'], 'returned_at': supplier['agreementReturnedAt']})
        api_client.unset_framework_agreement_returned(supplier['supplierId'], framework_slug, user)

    signed_agreements = filter(
        lambda x: re.search(r'/(\d+)-signed-framework-agreement.', x['path']),
        agreements_bucket.list('{}/agreements/'.format(framework_slug))
    )

    if supplier_ids is not None:
        signed_agreements = [
            agreement for agreement in signed_agreements
            if int(re.search(r'/(\d+)-signed-framework-agreement', agreement['path']).group(1)) in supplier_ids
        ]

    for document in signed_agreements:
        logger.info("Deleting {path}", extra={'path': document['path']})
        agreements_bucket.delete_key(document['path'])


def match_signed_agreements(supplier_ids, path):
    match = re.search(r'/(\d+)-signed-framework-agreement', path)
    return match and int(match.group(1)) in supplier_ids


if __name__ == '__main__':
    arguments = docopt(__doc__)
    stage = arguments['<stage>']
    framework_slug = arguments['<framework_slug>']
    data_api_access_token = arguments['--api-token']

    user = getpass.getuser()

    if arguments.get('<supplier_id_file>'):
        with open(arguments['<supplier_id_file>'], 'r') as f:
            supplier_ids = list(filter(None, [int(l.strip()) for l in f.readlines()]))
    else:
        supplier_ids = None

    main(stage, framework_slug, data_api_access_token, user, supplier_ids, arguments.get('<cutoff_time>'))
