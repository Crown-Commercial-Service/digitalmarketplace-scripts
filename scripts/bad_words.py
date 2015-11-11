"""

Usage:
    scripts/bad_words.py <data_api_url> <data_api_token> <bad_words_path> <framework_slug>
    <output_dir>
"""

import sys
import os
if sys.version_info > (3, 0):
    import csv
else:
    import unicodecsv as csv
import six
import re
from docopt import docopt
from dmutils.apiclient import DataAPIClient


def main(data_api_url, data_api_token, bad_words_path, framework_slug, output_dir):
    client = DataAPIClient(data_api_url, data_api_token)
    bad_words = get_bad_words(bad_words_path)
    suppliers = get_suppliers(client, framework_slug)
    check_services_with_bad_words(output_dir, framework_slug, client, suppliers, bad_words)


def get_suppliers(client, framework_slug):
    suppliers = client.find_framework_suppliers(framework_slug)
    suppliers = suppliers["supplierFrameworks"]
    if (framework_slug == "g-cloud-6"):
        suppliers_on_framework = suppliers
    else:
        suppliers_on_framework = [supplier for supplier in suppliers if supplier["onFramework"]]
    return suppliers_on_framework


def get_draft_services(client, supplier_id, framework_slug):
    services = client.find_draft_services(supplier_id, framework=framework_slug)
    services = services["services"]
    submitted_services = [service for service in services if service["status"] == "submitted"]
    return submitted_services


def get_services(client, supplier_id, framework_slug):
    services = client.find_services(supplier_id, framework=framework_slug)
    services = services["services"]
    return services


def get_bad_words(bad_words_path):
    with open(bad_words_path) as file:
        lines = file.readlines()
        return [line.strip() for line in lines if not (line.startswith("#") or line.isspace())]


def check_services_with_bad_words(output_dir, framework_slug, client, suppliers, bad_words):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open('{}/{}-services-with-blacklisted-words.csv'.format(
            output_dir, framework_slug), 'w') as csvfile:
        fieldnames = [
            'Supplier ID',
            'Framework',
            'Service ID',
            'Service Title',
            'Service Description',
            'Blacklisted Word Location',
            'Blacklisted Word Context',
            'Blacklisted Word',
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect='excel')
        writer.writeheader()
        for supplier in suppliers:
            if supplier["frameworkSlug"] == "g-cloud-6":
                services = get_services(client, supplier["supplierId"], supplier["frameworkSlug"])
            else:
                services = get_draft_services(client, supplier["supplierId"], supplier["frameworkSlug"])
            for service in services:
                for key in service:
                    if isinstance(service[key], six.string_types):
                        for word in bad_words:
                            if get_bad_words_in_value(word, service[key]):
                                output_bad_words(
                                    supplier["supplierId"], supplier["frameworkSlug"], service["id"],
                                    service["serviceName"], service["serviceSummary"], key,
                                    service[key], word, writer)
                    elif isinstance(service[key], list):
                        for contents in service[key]:
                            for word in bad_words:
                                if get_bad_words_in_value(word, contents):
                                    output_bad_words(
                                        supplier["supplierId"], supplier["frameworkSlug"], service["id"],
                                        service["serviceName"], service["serviceSummary"], key,
                                        contents, word, writer)


def get_bad_words_in_value(bad_word, value):
    if re.search(r"\b{}\b".format(bad_word), value, re.IGNORECASE):
        return True


def output_bad_words(
        supplier_id, framework, service_id, service_title,
        service_description, blacklisted_word_location,
        blacklisted_word_context, blacklisted_word, writer):
    row = {
        'Supplier ID': supplier_id,
        'Framework': framework,
        'Service ID': service_id,
        'Service Title': service_title,
        'Service Description': service_description,
        'Blacklisted Word Location': blacklisted_word_location,
        'Blacklisted Word Context': blacklisted_word_context,
        'Blacklisted Word': blacklisted_word,
        }
    writer.writerow(row)

if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(
        arguments['<data_api_url>'], arguments['<data_api_token>'], arguments['<bad_words_path>'],
        arguments['<framework_slug>'], arguments['<output_dir>'])
