from multiprocessing.pool import ThreadPool
from dmapiclient import HTTPError
from dmscripts.logging import configure_logger
import sys
if sys.version_info > (3, 0):
    import csv
else:
    import unicodecsv as csv


def buyer_requirements(client):
    def inner_function(user):
        try:
            briefs = client.find_briefs(user_id=user['id'])['briefs']
            if briefs:
                title_statuses = [u"; ".join([u"{} - {}".format(brief['title'], brief['status']) for brief in briefs])]
            else:
                title_statuses = []
        except HTTPError as e:
            title_statuses = []
            if e.status_code != 404:
                print("HTTP ERROR: {}".format(e))
        except Exception as e:
            title_statuses = []
            print("EXCEPTION: {}".format(e))

        return user, title_statuses

    return inner_function


def add_buyer_requirements(client, users):
    pool = ThreadPool(10)
    callback = buyer_requirements(client)
    return pool.imap_unordered(callback, users)


def find_buyer_users(client):
    for user in client.find_users_iter():
        if user['active'] and user['role'] == 'buyer':
            yield user


def list_buyers(client, output, include_briefs):
    writer = csv.writer(output, delimiter=',', quotechar='"')
    users = find_buyer_users(client)

    if include_briefs:
        users = add_buyer_requirements(client, users)
    else:
        users = ((user, None) for user in users)

    for user, briefs in users:
        row = [
            user['name'],
            user['emailAddress'],
            user['createdAt'],
        ]
        row += briefs if briefs else []
        writer.writerow(row)
