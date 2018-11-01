# -*- coding: utf-8 -*-
"""Helper classes for fetching supplier data given a client."""
from collections import OrderedDict
from datetime import date, timedelta
from functools import lru_cache
from itertools import groupby
import json

import backoff
import requests

from dmutils.formats import DISPLAY_DATE_FORMAT


class SupplierFrameworkData(object):
    """Class to get supplier data from the dmapiclient."""

    data = None

    def __init__(self, client, target_framework_slug):
        self.client = client
        self.target_framework_slug = target_framework_slug

    def get_supplier_frameworks(self):
        """Return supplier frameworks."""
        return self.client.find_framework_suppliers(self.target_framework_slug)['supplierFrameworks']

    def get_supplier_users(self):
        """Return a dict, {supplier id: [users]}."""
        users = self.client.export_users(self.target_framework_slug).get('users', [])

        def sort_by_func(d):
            return d['supplier_id']
        sorted_users = sorted(users, key=sort_by_func)
        return {k: list(g) for k, g in groupby(sorted_users, key=sort_by_func)}

    def get_supplier_draft_service_data(self, supplier_id):
        """Given a supplier ID return a list of dictionaries for services related to framework."""
        return self.client.find_draft_services_iter(supplier_id, framework=self.target_framework_slug)

    def populate_data(self):
        """Populate a dict with supplier data from the api."""
        self.data = self.get_supplier_frameworks()
        users = self.get_supplier_users()
        for supplier_framework in self.data:
            supplier_id = supplier_framework['supplierId']
            supplier_framework['users'] = users.get(supplier_id, [])
            supplier_framework['draft_services'] = list(self.get_supplier_draft_service_data(supplier_id))


class SuccessfulSupplierContextForNotify(SupplierFrameworkData):
    """Get the personalisation/ context for 'Your application result - if successful email'"""

    STATUS_MAP = {'submitted': 'Successful', 'not-submitted': 'No application', 'failed': 'Unsuccessful'}

    def __init__(self, client, target_framework_slug):
        """Get the target framework to operate on and list the lots.

        :param client: Instantiated api client
        :param target_framework_slug: Framework to fetch data for
        """
        self.date_today = date.today().strftime(DISPLAY_DATE_FORMAT)
        super(SuccessfulSupplierContextForNotify, self).__init__(client, target_framework_slug)

        self.framework = client.get_framework(self.target_framework_slug)['frameworks']
        self.framework_lots = [i['name'] for i in self.framework['lots']]

    def get_users_personalisations(self):
        """Return {email_address: {personalisations}} for users eligible for the
        'Your application result - if successful' email
        """
        output = {}
        for supplier_framework in filter(lambda i: i['onFramework'], self.data):
            for user in supplier_framework['users']:
                output.update(self.get_user_personalisation(user, supplier_framework))
        return output

    def get_lot_dict(self, supplier_framework):
        """Return a dict of lot status for each lot on the framework.
        """
        valid_lots = False

        lot_dict = OrderedDict((lot_name, 'No application') for lot_name in self.framework_lots)

        def sort_by_func(d):
            return d['lotName']
        sorted_draft_services = sorted(supplier_framework['draft_services'], key=sort_by_func)
        grouped_draft_services = groupby(sorted_draft_services, key=sort_by_func)
        for lotName, draft_services in grouped_draft_services:
            draft_services = list(draft_services)
            if any(draft_service['status'] == 'submitted' for draft_service in draft_services):
                status = 'submitted'
            elif any(draft_service['status'] == 'failed' for draft_service in draft_services):
                status = 'failed'
            else:
                status = 'not-submitted'
            if status == 'submitted':
                valid_lots = True
            lot_dict[lotName] = self.STATUS_MAP[status]
        if not valid_lots:
            return {}
        return lot_dict

    def get_user_personalisation(self, user, supplier_framework):
        """Get dict of all info required by template given a user and framework."""
        lot_dict = self.get_lot_dict(supplier_framework)
        if not lot_dict:
            return {}
        lot_dict = dict(list(zip(
            ['lot_%d' % i for i in range(1, len(self.framework_lots) + 1)],
            [' - '.join([k, v]) for k, v in lot_dict.items()]

        )))
        personalisation = {
            'date': self.date_today,
            'company_name': supplier_framework['supplierName'],
            'framework_name': self.framework['name'],
            'framework_slug': self.framework['slug'],
        }
        personalisation.update(lot_dict)
        return {user['email address']: personalisation}


class AppliedToFrameworkSupplierContextForNotify(SupplierFrameworkData):
    """Get the personalisation/ context for 'You application result - if successful email'"""

    def __init__(self, client, target_framework_slug, intention_to_award_at):
        """Get the target framework to operate on and list the lots.

        :param client: Instantiated api client
        :param target_framework_slug: Framework to fetch data for
        """
        super(AppliedToFrameworkSupplierContextForNotify, self).__init__(client, target_framework_slug)

        self.intention_to_award_at = intention_to_award_at
        self.framework = client.get_framework(self.target_framework_slug)['frameworks']

    def get_users_personalisations(self):
        """Return {email_address: {personalisations}} for all users who expressed interest in the framework
        """
        output = {}
        for supplier_framework in self.data:
            for user in supplier_framework['users']:
                output.update(self.get_user_personalisation(user))
        return output

    def get_user_personalisation(self, user):
        """Get dict of all info required by template given a user and framework."""
        personalisation = {
            'intention_to_award_at': self.intention_to_award_at,
            'framework_name': self.framework['name'],
            'framework_slug': self.framework['slug'],
            'applied': user['application_status'] == 'application'
        }
        return {user['email address']: personalisation}


class SupplierFrameworkDeclarations:

    def __init__(self, api_client, logger, framework_slug: str=None, dry_run: bool=True):
        self.api_client = api_client
        self.framework_slug = framework_slug
        self.dry_run = dry_run
        self.logger = logger

    def suppliers_application_failed_to_framework(self):
        """
        This functions calls the api endpoint and returns a list of the supplier_ids of suppliers that applied to be on
        the framework specified when the class was created but failed
        :return: A list of ints that are supplier_id
        :rtype: List[int]
        """
        return [
            framework_supplier['supplierId']
            for framework_supplier in self.api_client.find_framework_suppliers_iter(self.framework_slug)
            if framework_supplier['onFramework'] is not True
        ]

    def remove_declaration(self, supplier_id: int, framework_slug: str):
        """
        This method accesses an endpoint and removes the declaration of the associated SupplierFramework. It returns
        either the response object from the endpoint, or throws an exception
        :param supplier_id: the identifier for the supplier whose declaration should be removed
        :type supplier_id: int
        :param framework_slug: the string representation of the framework to be used
        :type framework_slug: str
        :return: response from endpoint
        :rtype: Dict
        """
        if self.dry_run:
            self.logger.info("Would remove declaration from suppler with id %s that applied to framework %s",
                             supplier_id, framework_slug
                             )
        else:
            return self.api_client.remove_supplier_declaration(supplier_id, framework_slug, 'user')

    def remove_declaration_from_failed_applicants(self):
        """
        This method gets a list of failed applicants and then calls the remove_declaration function for each one. It
        returns None.
        :return: None
        :rtype: None
        """
        failed_supplier_ids = self.suppliers_application_failed_to_framework()
        for supplier_id in failed_supplier_ids:
            self.remove_declaration(supplier_id)

    def _frameworks_older_than_date(self, date_closed):
        """
        Returns a list of the slugs of frameworks that closed prior to the date passed to the method
        :param date_closed: the method will return frameworks that closed prior to this value
        :type date_closed: date
        :return: list of framework slugs
        :rtype: List[str]
        """
        all_frameworks = self.api_client.find_frameworks()
        return [framework['slug'] for framework in all_frameworks if framework['frameworkExpiresAtUTC'] <= date_closed]

    def remove_declaration_from_suppliers(self, date_from=None):
        """
        Gets a list of all suppliers on all frameworks older than 'date_from' and removes their declarations
        :param date_from: the date before which declarations should be removed
        :type date_from: datetime
        :return: None
        :rtype: None
        """
        if not date_from:
            date_from = date.today() - timedelta(365 * 3)
        old_frameworks = self._frameworks_older_than_date(date_from)
        for framework in old_frameworks:
            suppliers_with_declarations_to_clear = self.api_client.find_framework_suppliers(
                framework_slug=framework
            )['supplierFrameworks']
            for supplier in suppliers_with_declarations_to_clear:
                self.remove_declaration(supplier['supplierId'], framework_slug=framework)


def get_supplier_ids_from_file(supplier_id_file):
    if not supplier_id_file:
        return None
    with open(supplier_id_file, 'r') as f:
        return list(map(int, [_f for _f in [l.strip() for l in f.readlines()] if _f]))


@lru_cache()
@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
def country_code_to_name(country_code):
    register, code = country_code.split(':')

    register_response = requests.get(f'https://{register}.register.gov.uk/records/{code}.json')
    if register_response.status_code == 200:
        record = json.loads(register_response.text)
        return record[code]['item'][0]['name']

    raise requests.exceptions.RequestException(register_response)
