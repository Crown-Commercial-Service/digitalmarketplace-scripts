#!/usr/bin/env python
"""
Our data retention policy states that unsuccessful suppliers have their declarations deleted. This ensures that, in the
case of a breach, data that is commercially sensitive would not be exposed. We do this through calls to the api
endpoint on /suppliers/<supplier_id>/frameworks/>framework_slug>

This script gets all the suppliers that can have their declarations removed because they did not get onto a
specified framework, identifies their ids, and then calls the endpoint to remove the declaration
"""
import sys

sys.path.insert(0, '.')


class SupplierFrameworkMethods:

    def __init__(self, api_client, framework_slug: str):
        self.api_client = api_client
        self.framework_slug = framework_slug

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

    def remove_declaration(self, supplier_id: int):
        """
        This method accesses an endpoint and removes the declaration of the associated SupplierFramework.
        :param supplier_id: the identifier for the supplier whose declaration should be removed
        :type supplier_id: int
        :return: True if successful; else False
        :rtype: bool
        """
        response = self.api_client.remove_supplier_declaration(supplier_id, self.framework_slug, 'user')
        if response.status_code == 200:
            return True
        else:
            return False


def main():
    pass


if __name__ == '__main__':
    main()
