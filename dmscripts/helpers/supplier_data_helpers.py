# -*- coding: utf-8 -*-
"""Helper classes for fetching supplier data given a client."""
from collections import OrderedDict
from datetime import date, timedelta, datetime
from functools import lru_cache
from typing import List

from dmapiclient import DataAPIClient
from dmapiclient.audit import AuditTypes
from itertools import groupby
from operator import itemgetter

import json

import backoff
import requests

from dmutils.dates import update_framework_with_formatted_dates
from dmutils.email.helpers import hash_string
from dmutils.formats import DISPLAY_DATE_FORMAT, DATETIME_FORMAT


class SupplierFrameworkData(object):
    """Class to get supplier data from the dmapiclient."""

    data = None

    def __init__(self, client, target_framework_slug, *, supplier_ids=None, logger=None):
        """
        :param client: Client object for the Digital Marketplace API
        :param target_framework_slug str: Framework slug
        :param supplier_ids: List of supplier IDs to filter data by
        """
        self.client = client
        self.target_framework_slug = target_framework_slug
        self.supplier_ids = supplier_ids
        self.logger = logger

    def get_supplier_frameworks(self):
        """Return supplier frameworks."""
        framework_suppliers = self.client.find_framework_suppliers_iter(
            self.target_framework_slug, with_declarations=None
        )
        if self.supplier_ids:
            framework_suppliers = (s for s in framework_suppliers if s["supplierId"] in self.supplier_ids)
        return list(framework_suppliers)

    def get_supplier_users(self):
        """Return a dict, {supplier id: [users]}."""
        users = self.client.export_users(self.target_framework_slug).get('users', [])

        keyfunc = itemgetter("supplier_id")
        if self.supplier_ids:
            users = (u for u in users if u["supplier_id"] in self.supplier_ids)
        users = sorted(users, key=keyfunc)
        return {k: list(g) for k, g in groupby(users, key=keyfunc)}

    def get_supplier_draft_service_data(self, supplier_id):
        """Given a supplier ID return a list of dictionaries for services related to framework."""
        return self.client.find_draft_services_iter(supplier_id, framework=self.target_framework_slug)

    def populate_data(self):
        """Populate a dict with supplier data from the api."""
        self.data = self.get_supplier_frameworks()
        supplier_count = len(self.data)
        users = self.get_supplier_users()
        for supplier_number, supplier_framework in enumerate(self.data, start=1):
            if self.logger:
                self.logger.info(f"Populating data for supplier {supplier_number} of {supplier_count}")
            supplier_id = supplier_framework['supplierId']
            supplier_framework['users'] = users.get(supplier_id, [])
            supplier_framework['draft_services'] = list(self.get_supplier_draft_service_data(supplier_id))


class SuccessfulSupplierContextForNotify(SupplierFrameworkData):
    """Get the personalisation/ context for 'Your application result - if successful email'"""

    STATUS_MAP = {'submitted': 'Successful', 'not-submitted': 'No application', 'failed': 'Unsuccessful'}

    def __init__(self, client, target_framework_slug, *, supplier_ids=None, logger=None):
        """Get the target framework to operate on and list the lots.

        :param client: Instantiated api client
        :param target_framework_slug: Framework to fetch data for
        :param supplier_ids: List of supplier IDs to filter data by
        """
        self.date_today = date.today().strftime(DISPLAY_DATE_FORMAT)
        super(SuccessfulSupplierContextForNotify, self).__init__(
            client, target_framework_slug, supplier_ids=supplier_ids, logger=logger)

        self.framework = client.get_framework(self.target_framework_slug)['frameworks']
        self.framework_lots = [i['name'] for i in self.framework['lots']]

    def get_users_personalisations(self):
        """Return {email_address: {personalisations}} for users eligible for the
        'Your application result - if successful' email
        """
        suppliers_on_framework = list(filter(lambda i: i['onFramework'], self.data))
        supplier_count = len(suppliers_on_framework)

        output = {}
        for supplier_number, supplier_framework in enumerate(suppliers_on_framework, start=1):
            if self.logger:
                self.logger.info(
                    f"Building user personalisations for supplier {supplier_number} of {supplier_count}: "
                    f"{supplier_framework['supplierId']}"
                )
            for user in supplier_framework['users']:
                output.update(self.get_user_personalisation(user, supplier_framework))
            primary_email_address = supplier_framework.get('declaration', {}).get('primaryContactEmail')
            if primary_email_address and primary_email_address not in output:
                output.update(
                    self.get_user_personalisation({'email address': primary_email_address}, supplier_framework)
                )
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

    def __init__(self, client, target_framework_slug, *, intention_to_award_at=None, supplier_ids=None):
        """Get the target framework to operate on and list the lots.

        :param client: Instantiated api client
        :param target_framework_slug str: Framework to fetch data for
        :param intention_to_award_at: Date at which framework agreements will be awarded
        :param supplier_ids: List of supplier IDs to fetch data for
        """
        super().__init__(client, target_framework_slug, supplier_ids=supplier_ids)

        self.framework = self.client.get_framework(self.target_framework_slug)["frameworks"]
        update_framework_with_formatted_dates(self.framework)
        if intention_to_award_at is None:
            self.intention_to_award_at = self.framework["intentionToAwardAt"]
        else:
            self.intention_to_award_at = intention_to_award_at

    def get_users_personalisations(self):
        """Return {email_address: {personalisations}} for all users who expressed interest in the framework
        """
        output = {}
        for supplier_framework in self.data:
            for user in supplier_framework['users']:
                output.update(self.get_user_personalisation(user))
        return output

    def get_suppliers_with_users_personalisations(self):
        """
        Return an iterator of supplier user email personalisations, grouped by supplier IDs.
        :rtype: Iterator[Tuple[int, Iterator[Tuple[Dict, Dict[str, str]]]]]]
        """
        return (
            (
                int(supplier["supplierId"]),
                (
                    (user, self.get_user_personalisation(user)[user["email address"]]) for user in supplier["users"]
                ),
            ) for supplier in self.data
        )

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
    """
    Methods for manipulating supplier declarations
    """

    def __init__(self, api_client, logger, dry_run, user):
        self.api_client = api_client
        self.dry_run = dry_run
        self.logger = logger
        self.user = user  # passed through by the script that calls this

    def suppliers_application_failed_to_framework(self, framework_slug):
        """
        This functions calls the api endpoint and returns a list of the supplier_ids of suppliers that applied to be on
        the framework specified when the class was created but failed
        :return: A list of ints that are supplier_id
        :rtype: List[int]
        """
        return [
            framework_supplier['supplierId']
            for framework_supplier in self.api_client.find_framework_suppliers_iter(
                framework_slug, with_declarations=None
            )
            if framework_supplier['onFramework'] is not True
        ]

    def remove_declaration(self, supplier_id, framework_slug):
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
            self.logger.info(
                f"Declaration of supplier {supplier_id} "
                f"that applied to framework {framework_slug} removed"
            )
            return self.api_client.remove_supplier_declaration(
                supplier_id,
                framework_slug,
                user=f'{self.user} {datetime.now().isoformat()}'
            )

    def remove_declaration_from_failed_applicants(self, framework_slug):
        """
        This method gets a list of failed applicants and then calls the remove_declaration function for each one. It
        returns None.
        :return: None
        :rtype: None
        """
        failed_supplier_ids = self.suppliers_application_failed_to_framework(framework_slug)
        for supplier_id in failed_supplier_ids:
            self.remove_declaration(supplier_id, framework_slug)

    def _frameworks_older_than_date(self, date_closed):
        """
        Returns a list of the slugs of frameworks that closed prior to the date passed to the method
        :param date_closed: the method will return frameworks that closed prior to this value
        :type date_closed: date
        :return: list of framework slugs
        :rtype: List[str]
        """
        all_frameworks = self.api_client.find_frameworks()["frameworks"]
        return [
            framework['slug'] for framework in all_frameworks
            if datetime.strptime(framework['frameworkExpiresAtUTC'], DATETIME_FORMAT) <= date_closed]

    def remove_supplier_declaration_for_expired_frameworks(self):
        """
        Gets a list of all suppliers on all frameworks older than three years and removes their declarations
        :return: None
        :rtype: None
        """
        date_from = datetime.today() - timedelta(365 * 3)
        old_frameworks = self._frameworks_older_than_date(date_from)
        for framework in old_frameworks:
            suppliers_with_declarations_to_clear = self.api_client.find_framework_suppliers_iter(
                framework_slug=framework, with_declarations=None
            )
            for supplier in suppliers_with_declarations_to_clear:
                self.remove_declaration(supplier['supplierId'], framework_slug=framework)
        self.logger.info("All declarations older than three years have been cleared")


def get_supplier_ids_from_file(supplier_id_file):
    if not supplier_id_file:
        return None
    with open(supplier_id_file, 'r') as f:
        return list(map(int, [_f for _f in [l.strip() for l in f.readlines()] if _f]))


def get_supplier_ids_from_args(args):
    if args["--supplier-ids-from"]:
        supplier_ids = get_supplier_ids_from_file(args["--supplier-ids-from"])
    elif args["--supplier-id"]:
        try:
            supplier_ids = (ids.split(",") for ids in args["--supplier-id"])
            supplier_ids = (int(id) for ids in supplier_ids for id in ids)
            supplier_ids = list(supplier_ids)
        except ValueError:
            raise TypeError("arguments to --supplier-id should be integers or comma-separated lists of integers")
    else:
        supplier_ids = None

    return supplier_ids


@lru_cache()
@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3)
def country_code_to_name(country_code):
    register, code = country_code.split(':')

    register_response = requests.get(f'https://{register}.register.gov.uk/records/{code}.json')
    if register_response.status_code == 200:
        record = json.loads(register_response.text)
        return record[code]['item'][0]['name']

    raise requests.exceptions.RequestException(register_response)


def unsuspend_suspended_supplier_services(record, suspending_user, client, logger, dry_run):
    """
    This method checks if the supplier has services suspended by the suspending_user, if so it un-suspends them.
    :param record: augmented supplier record object generated by countersigning script
    :param suspending_user: user name of user who performed automated suspension
    :param client: API client
    :param logger: logger
    :param dry_run: bool
    :return: None
    :rtype: None
    """
    new_service_status, old_service_status = 'published', 'disabled'
    framework_slug = record['frameworkSlug']
    supplier_id = record["supplier_id"]
    suspended_services_on_framework = set(
        service["id"] for service in
        client.find_services(
            supplier_id=supplier_id, framework=framework_slug, status=old_service_status
        )["services"]
    )
    if not suspended_services_on_framework:
        logger.info(f'Supplier {record["supplier_id"]} has no {old_service_status} services on the framework.')

    services_suspended_by_script = set(
        event["data"]["serviceId"]
        for event in
        client.find_audit_events_iter(
            audit_type=AuditTypes.update_service_status,
            data_supplier_id=supplier_id,
            user=suspending_user
        )
    )
    service_ids = suspended_services_on_framework & services_suspended_by_script
    # Unsuspend all services for supplier (the API will re-index the services for search results)
    if service_ids:
        logger.info(
            f"Setting {len(service_ids)} services to '{new_service_status}' for supplier {supplier_id}."
        )
    for service_id in service_ids:
        if dry_run:
            logger.info(f"[DRY RUN] Would unsuspend service {service_id} for supplier {supplier_id}")
        else:
            client.update_service_status(service_id, new_service_status, "Unsuspend services helper")


def get_email_addresses_for_supplier(api_client: DataAPIClient, supplier_id: int) -> List[str]:
    """
    Get the email addresses for each user belonging to `supplier_id`. Use `SupplierFrameworkData.get_supplier_users`
    instead if you need to get email addresses for a large number of suppliers.
    """
    supplier_users = api_client.find_users_iter(supplier_id=supplier_id, personal_data_removed=False)
    return [user["emailAddress"] for user in supplier_users if user["active"]]


def send_email_to_all_users_of_suppliers(
        api_client,
        mail_client,
        supplier_ids,
        notify_template,
        logger,
        *,
        personalisation=None,
        is_dry_run=False,
):
    email_addresses = [
        supplier_user
        for supplier_id in supplier_ids
        for supplier_user in get_email_addresses_for_supplier(api_client, supplier_id)
    ]

    prefix = "[Dry Run] " if is_dry_run else ""
    user_count = len(email_addresses)

    for user_number, email in enumerate(email_addresses, start=1):
        logger.info(
            f"{prefix}Sending email to supplier user {user_number} of {user_count}: {hash_string(email)}"
        )
        if not is_dry_run:
            mail_client.send_email(
                to_email_address=email,
                template_name_or_id=notify_template,
                personalisation=personalisation,
            )
