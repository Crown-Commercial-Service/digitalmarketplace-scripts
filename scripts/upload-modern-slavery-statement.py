#!/usr/bin/env python3
"""
Usage:
    scripts/upload-modern-slavery-statement.py
        <file_path> <supplier_id> <framework> <s3_file_name> [<stage>]

Options:
    -h --help   Show this screen.

Parameters:
    <file_path>    Local path of modern slavery statement file.
    <supplier_id>  Supplier ID
    <framework>    Framework
    <s3_file_name> The file name that users will see. For example, 'modern-slavery-statement-2020-11-19.pdf'
    <stage>        Stage. Defaults to production.
"""
from dmapiclient import DataAPIClient
from docopt import docopt
from dmutils.env_helpers import get_api_endpoint_from_stage
from dmutils.s3 import S3
import sys

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.helpers.updated_by_helpers import get_user


def get_slavery_statement_declaration_key(declaration):
    if declaration['declaration'].get('modernSlaveryStatement'):
        return 'modernSlaveryStatement'

    return 'modernSlaveryStatementOptional'


if __name__ == '__main__':
    arguments = docopt(__doc__)

    file_path = arguments['<file_path>']
    supplier_id = arguments['<supplier_id>']
    framework = arguments['<framework>']
    s3_file_name = arguments['<s3_file_name>']
    stage = arguments['<stage>'] or 'production'

    bucket_name = f"digitalmarketplace-documents-{stage}-{stage}"
    s3_key_name = f"{framework}/documents/{supplier_id}/{s3_file_name}"
    asset_url = f"https://assets.digitalmarketplace.service.gov.uk/{s3_key_name}"

    user = get_user()
    print(f"Setting user to '{user}'...")

    data_api_client = DataAPIClient(get_api_endpoint_from_stage(stage), get_auth_token('api', stage), user=user)
    supplier_declaration = data_api_client.get_supplier_declaration(supplier_id, framework)

    bucket = S3(bucket_name)
    with open(file_path, 'br') as source_file:
        bucket.save(s3_key_name, source_file, acl='public-read')
    print(f"Uploaded {file_path} to {bucket.bucket_name}::{s3_key_name}")

    data_api_client.update_supplier_declaration(
        supplier_id=supplier_id,
        framework_slug=framework,
        declaration_update={
            get_slavery_statement_declaration_key(supplier_declaration): asset_url
        }
    )

    print("Updated modern slavery statement. If G-Cloud, check the link in one of the supplier's services.")
