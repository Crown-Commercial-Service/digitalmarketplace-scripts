from functools import partial
import time
from multiprocessing.pool import ThreadPool

from dmapiclient import HTTPError

import sys
if sys.version_info > (3, 0):
    import csv
else:
    import unicodecsv as csv


def suppliers_generator(data_api_client):
    for supplier in data_api_client.find_suppliers_iter():
        yield supplier


def execute_concurrently(callback, iterable_thing):
    pool = ThreadPool(10)
    return pool.imap_unordered(callback, iterable_thing)


def filter_list_of_dicts_by_value(list_of_dicts, key_to_match, expected_value):
    return [
        dic for dic in list_of_dicts
        if dic.get(key_to_match) == expected_value
    ]


def get_all_supplier_framework_info(data_api_client, framework_slug, suppliers):

    def get_supplier_framework_info(enumerated_supplier):
        """
        Returns a supplier_framework or None if no supplier_framework entry exists
        :param enumerated_supplier: tuple formatted (index, supplier)
        :return: a supplier_framework or None
        """
        index, supplier = enumerated_supplier
        if index % 100 == 0:
            print('~{} suppliers'.format(index))
        try:
            supplier_framework = data_api_client.get_supplier_framework_info(supplier['id'], framework_slug)
            return supplier_framework.get('frameworkInterest')
        except HTTPError:
            return None

    # filters Nones and entries with { 'onFramework': None } from a list
    return [
        supplier_framework for supplier_framework
        in execute_concurrently(get_supplier_framework_info, enumerate(suppliers))
        if (supplier_framework is not None) and (supplier_framework.get('onFramework') is not None)
    ]


def find_all_users_given_supplier_frameworks(data_api_client, supplier_frameworks):

    def find_users_given_supplier_frameworks(total_supplier_frameworks, enumerated_supplier_framework):
        """
        Returns a list of users for each supplier.
        :param total_supplier_frameworks: total number of supplier_frameworks gotten from API
        :param enumerated_supplier_framework: tuple formatted (index, supplier_framework)
        :return: a list of users for a supplier
        """
        index, supplier_framework = enumerated_supplier_framework
        if (total_supplier_frameworks - index) % 100 == 0:
            print('~{} supplier_frameworks remaining'.format(total_supplier_frameworks - index))

        supplier_users = data_api_client.find_users(supplier_id=supplier_framework['supplierId']).get('users')
        for supplier_user in supplier_users:
            supplier_user['supplier']['onFramework'] = supplier_framework['onFramework']
            supplier_user['supplier']['agreementReturned'] = supplier_framework['agreementReturned']

        return supplier_users

    callback = partial(find_users_given_supplier_frameworks, len(supplier_frameworks))
    # flattens a list of lists
    return [
        user for users_for_one_supplier
        in execute_concurrently(callback, enumerate(supplier_frameworks))
        for user in users_for_one_supplier
    ]


def list_users(data_api_client, output, framework_slug, on_framework=None, agreement_returned=None):
    start_time = time.time()
    writer = csv.writer(output, delimiter=',', quotechar='"')

    suppliers = suppliers_generator(data_api_client)
    supplier_frameworks = get_all_supplier_framework_info(data_api_client, framework_slug, suppliers)
    print('{} total supplier_frameworks in {}s'.format(len(supplier_frameworks), time.time() - start_time))

    # filtering
    if on_framework is not None:
        supplier_frameworks = filter_list_of_dicts_by_value(
            supplier_frameworks, 'onFramework', on_framework)

    if agreement_returned is not None:
        supplier_frameworks = filter_list_of_dicts_by_value(
            supplier_frameworks, 'agreementReturned', agreement_returned)

    # get all users w/ a bit of extra data
    users = find_all_users_given_supplier_frameworks(data_api_client, supplier_frameworks)
    print('{} total users in {}s'.format(len(users), time.time() - start_time))

    for user in users:
        row = [
            'pass' if user['supplier']['onFramework'] else 'fail',
            'returned' if user['supplier']['agreementReturned'] else 'not returned',
            user['emailAddress'],
            user['name'],
            user['supplier']['supplierId'],
            user['supplier']['name']
        ]
        writer.writerow(row)
