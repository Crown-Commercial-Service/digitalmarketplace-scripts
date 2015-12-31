from multiprocessing.pool import ThreadPool
from dmapiclient import HTTPError
import sys
if sys.version_info > (3, 0):
    import csv
else:
    import unicodecsv as csv


def selection_status(client, framework_slug):
    def inner_function(user):
        try:
            declaration = client.get_supplier_declaration(
                user['supplier']['supplierId'], framework_slug
            )['declaration']
            if declaration:
                status = declaration['status']
            else:
                status = 'unstarted'
        except HTTPError as e:
            if e.status_code == 404:
                status = 'unstarted'
            else:
                status = 'error-{}'.format(e.status_code)
        except KeyError:
            status = 'error-key-error'
        return (status, user)

    return inner_function


def add_selection_status(client, framework_slug, users):
    pool = ThreadPool(10)
    callback = selection_status(client, framework_slug)
    return pool.imap_unordered(callback, users)


def filter_is_registered_with_framework(client, framework_slug, users):
    registered_suppliers = client.get_interested_suppliers(framework_slug).get('interestedSuppliers', None)
    interested_users = (user for user in users
                        if user['supplier']['supplierId'] in registered_suppliers)
    return interested_users


def find_supplier_users(client):
    for user in client.find_users_iter():
        if user['active'] and user['role'] == 'supplier':
            yield user


def list_users(client, output, framework_slug, include_status):
    writer = csv.writer(output, delimiter=',', quotechar='"')
    users = find_supplier_users(client)
    if framework_slug is not None:
        users = filter_is_registered_with_framework(client, framework_slug, users)
    if include_status:
        users = add_selection_status(client, framework_slug, users)
    else:
        users = ((None, user) for user in users)

    for status, user in users:
        row = [] if status is None else [status]
        row += [
            user['emailAddress'],
            user['name'],
            user['supplier']['supplierId'],
            user['supplier']['name']
        ]
        writer.writerow(row)
