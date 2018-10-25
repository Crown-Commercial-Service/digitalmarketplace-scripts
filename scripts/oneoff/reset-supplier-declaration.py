#!/usr/bin/env python3

"""
A one-off script for resetting a supplier's declarations after a temporary bug affected the G-Cloud 10 application
process, preventing suppliers from copying over answers from their G-Cloud 9 declaration.

You can reset a declaration either by providing the email address of a user associated with that supplier, or by
directly using the supplier's id.

Syntax: ./scripts/oneoff/reset-supplier-declaration.py --stage preview --email 12345@user.marketplace.team
        ./scripts/oneoff/reset-supplier-declaration.py --stage preview --supplier-id 123456
"""

import getpass
import sys

import argparse

sys.path.insert(0, '.')

from dmapiclient import DataAPIClient
from dmapiclient.errors import HTTPError
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage


def reset_supplier_declaration(stage, framework_slug, reason, email, supplier_id):
    data_api_token = get_auth_token('api', stage) if stage != 'development' else 'myToken'
    data_api_client = DataAPIClient(get_api_endpoint_from_stage(stage), data_api_token)

    if email:
        user = data_api_client.get_user(email_address=email)

        if not user:
            print(f'No user found for email address `{email}`')
            exit(1)

        user_supplier_id = user['users']['supplier']['supplierId']
        if user_supplier_id and supplier_id and user_supplier_id != supplier_id:
            print(f'Email address provided does not match with supplier provided. Email address `{email}` is '
                  f'associated with supplierId `{supplier_id}`. Script was called with supplierId `{supplier_id}`.')
            exit(2)

        supplier_id = user_supplier_id

    try:
        supplier_framework = data_api_client.get_supplier_framework_info(supplier_id=supplier_id,
                                                                         framework_slug=framework_slug)
        print(f"Current supplier declaration: {supplier_framework['frameworkInterest']['declaration']}")

    except HTTPError:
        print(f'No supplier framework found for supplierId `{supplier_id}` on framework `{framework_slug}`.')
        exit(3)

    if not supplier_framework:
        print(f'No supplier framework/interest record found for supplierId `{supplier_id}` on framework '
              f'`{framework_slug}`.')
        exit(4)

    data_api_client.set_supplier_declaration(supplier_id=supplier_id, framework_slug=framework_slug, declaration={},
                                             user=f'{getpass.getuser()} - {reason}')
    data_api_client.set_supplier_framework_prefill_declaration(supplier_id=supplier_id, framework_slug=framework_slug,
                                                               prefill_declaration_from_framework_slug=None,
                                                               user=f'{getpass.getuser()} - {reason}')
    print(f'Supplier declaration for supplierId `{supplier_id}` on framework `{framework_slug}` has been reset.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', default='development', choices=['development', 'preview', 'staging', 'production'],
                        nargs='?',
                        help="Which stage's API to communicate with.")
    parser.add_argument('--email', type=str,
                        help="The email address of the requesting user's account. This will be used to lookup which "
                             "supplier's declaration needs to be reset.")
    parser.add_argument('--supplier-id', type=int,
                        help="Which supplier's declaration to reset.")
    parser.add_argument('--framework-slug', type=str, default='g-cloud-10',
                        help="Which framework's supplier declaration should be targeted.")
    parser.add_argument('--reason', type=str,
                        default='Reset supplier declaration to allow re-use of answers from G-Cloud 9 to G-Cloud 10',
                        help="Include a justification/reason for resetting that supplier's declaration.")

    args = parser.parse_args()

    reset_supplier_declaration(stage=args.stage.lower(), framework_slug=args.framework_slug, reason=args.reason,
                               email=args.email, supplier_id=args.supplier_id)
