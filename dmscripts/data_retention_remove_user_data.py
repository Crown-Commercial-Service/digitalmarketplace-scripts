#!/usr/bin/env python
"""
Our data retention policy states that unsuccessful suppliers have their declarations deleted. This ensures that, in the
case of a breach, data that is commercially sensitive would not be exposed. We do this through calls to the api
endpoint on /suppliers/<supplier_id>/frameworks/>framework_slug>

This script gets all the suppliers that can have their declarations removed because they did not get onto a
specified framework, identifies their ids, and then calls the endpoint to remove the declaration
"""
from dmscripts.helpers.supplier_data_helpers import SupplierFrameworkDeclarations
from datetime import datetime


def remove_user_data(data_api_client, logger, dry_run: bool, cutoff_date):
    prefix = '[DRY RUN]: ' if dry_run else ''
    all_users = list(data_api_client.find_users_iter(personal_data_removed=False))

    for user in all_users:
        last_logged_in_at = datetime.strptime(user['loggedInAt'], '%Y-%m-%dT%H:%M:%S.%fZ')
        if last_logged_in_at < cutoff_date and not user['personalDataRemoved']:
            logger.warn(
                f"{prefix}Removing personal data for user: {user['id']}"
            )
            if not dry_run:
                data_api_client.remove_user_personal_data(
                    user['id'],
                    'Data Retention Script {}'.format(datetime.now().isoformat())
                )


def remove_supplier_data(data_api_client, logger, dry_run: bool, cutoff_date):
    supplier_frameworks = SupplierFrameworkDeclarations(
        api_client=data_api_client,
        logger=logger,
        dry_run=dry_run
    )
    supplier_frameworks.remove_declaration_from_suppliers(cutoff_date)
