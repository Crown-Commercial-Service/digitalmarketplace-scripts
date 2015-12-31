from __future__ import unicode_literals

from dmapiclient import HTTPError

import sys
if sys.version_info > (3, 0):
    import csv
else:
    import unicodecsv as csv


def insert_result(client, supplier_id, supplier_name, framework_slug, result, user):
    try:
        dm_supplier_name = client.get_supplier(supplier_id)['suppliers']['name']
        if supplier_name == dm_supplier_name:
            client.set_framework_result(supplier_id, framework_slug, result, user)
            return "OK: {}\n".format(supplier_id)
        else:
            return "Error: Supplier name '{}' does not match '{}' for supplier ID {}\n".format(
                supplier_name,
                dm_supplier_name,
                supplier_id
            )
    except HTTPError as e:
        return "Error inserting result for {} ({}): {}\n".format(supplier_id, result, str(e))


def insert_results(client, output, framework_slug, filename, user):
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for index, row in enumerate(reader, start=1):
            try:
                supplier_id = int(row[0])
                supplier_name = row[1].strip()
                result = row[2].strip().lower()
                if result == 'pass':
                    result = True
                elif result == 'fail':
                    result = False
                else:
                    raise Exception("Result must be 'pass' or 'fail', not '{}'".format(result))
            except Exception as e:
                output.write("Error: {}; Bad line: {}\n".format(str(e), index))
                continue

            output.write(insert_result(client, supplier_id, supplier_name, framework_slug, result, user))
