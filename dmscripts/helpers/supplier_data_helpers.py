# -*- coding: utf-8 -*-
"""Helper classes for fetching supplier data given a client."""
from collections import OrderedDict
from datetime import date
from itertools import groupby

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
        sort_by_func = lambda i: i['supplier_id']
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

        sort_by_func = lambda i: i['lotName']
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

    def __init__(self, client, target_framework_slug, successful_notification_date):
        """Get the target framework to operate on and list the lots.

        :param client: Instantiated api client
        :param target_framework_slug: Framework to fetch data for
        """
        super(AppliedToFrameworkSupplierContextForNotify, self).__init__(client, target_framework_slug)

        self.successful_notification_date = successful_notification_date
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
            'successful_notification_date': self.successful_notification_date,
            'framework_name': self.framework['name'],
            'framework_slug': self.framework['slug'],
            'applied': user['application_status'] == 'application'
        }
        return {user['email address']: personalisation}


def get_supplier_ids_from_file(supplier_id_file):
    if not supplier_id_file:
        return None
    with open(supplier_id_file, 'r') as f:
        return list(map(int, [_f for _f in [l.strip() for l in f.readlines()] if _f]))
