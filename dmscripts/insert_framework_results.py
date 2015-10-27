from __future__ import unicode_literals
import unicodecsv as csv

from dmutils.apiclient.errors import HTTPError


def insert_result(client, supplier_id, framework_slug, result, user):
    try:
        client.set_framework_result(supplier_id, framework_slug, result, user)
        return "OK: {}\n".format(supplier_id)
    except HTTPError as e:
        return "Error inserting result for {} ({}): {}\n".format(supplier_id, result, str(e))


def insert_results(client, output, framework_slug, filename, user):
    with open(filename, 'rb') as csvfile:
        reader = csv.reader(csvfile)
        for index, row in enumerate(reader, start=1):
            try:
                supplier_id = int(row[0])
                result = row[1].strip().lower()
                if result == 'pass':
                    result = True
                elif result == 'fail':
                    result = False
                else:
                    raise Exception("Result must be 'pass' or 'fail', not '{}'".format(result))
            except Exception as e:
                output.write("Error: {}; Bad line: {}\n".format(str(e), index))
                continue

            output.write(insert_result(client, supplier_id, framework_slug, result, user))
