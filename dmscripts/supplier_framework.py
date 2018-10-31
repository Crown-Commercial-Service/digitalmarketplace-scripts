#!/usr/bin/env python
"""
Our data retention policy states that unsuccessful suppliers have their declarations deleted. This ensures that, in the
case of a breach, data that is commercially sensitive would not be exposed. We do this through calls to the api
endpoint on /suppliers/<supplier_id>/frameworks/>framework_slug>

This script gets all the suppliers that can have their declarations removed because they did not get onto a
specified framework, identifies their ids, and then calls the endpoint to remove the declaration
"""
from datetime import date, timedelta


class SupplierFrameworkMethods:

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
            if framework_supplier['onFramework'] == 'False'
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
