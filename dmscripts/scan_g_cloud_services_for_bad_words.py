import csv
import re
from collections import Counter

CSV_FIELD_NAMES = [
    'Supplier ID',
    'Framework',
    'Service ID',
    'Service Name',
    'Service Description',
    'Blacklisted Word Location',
    'Blacklisted Word Context',
    'Blacklisted Word',
]


def get_suppliers(client, framework_slug):
    suppliers = client.find_framework_suppliers(framework_slug)
    suppliers = suppliers["supplierFrameworks"]
    if framework_slug == "g-cloud-6":
        suppliers_on_framework = suppliers
    else:
        suppliers_on_framework = [supplier for supplier in suppliers if supplier["onFramework"]]
    return suppliers_on_framework


def get_services(client, supplier_id, framework_slug, scan_drafts):
    if scan_drafts:
        return client.find_draft_services(supplier_id, framework=framework_slug)['services']

    return client.find_services(supplier_id, framework=framework_slug)["services"]


def _get_bad_words_from_file(bad_words_path):
    with open(bad_words_path) as file:
        lines = file.readlines()
        return [line.strip() for line in lines if not (line.startswith("#") or line.isspace())]


def _get_bad_words_in_value(bad_word, value):
    if re.search(r"\b{}\b".format(bad_word), value, re.IGNORECASE):
        return True


def output_bad_words(
    supplier_id,
    framework,
    service_id,
    service_name,
    service_description,
    blacklisted_word_location,
    blacklisted_word_context,
    blacklisted_word,
    writer,
    logger,
):
    row = {
        'Supplier ID': supplier_id,
        'Framework': framework,
        'Service ID': service_id,
        'Service Name': service_name,
        'Service Description': service_description,
        'Blacklisted Word Location': blacklisted_word_location,
        'Blacklisted Word Context': blacklisted_word_context,
        'Blacklisted Word': blacklisted_word,
    }
    logger.info("{} - {}".format(blacklisted_word, service_id))
    writer.writerow(row)


BAD_WORDS_COUNTER = Counter()


def check_services_with_bad_words(
    output_file_path, framework_slug, client, suppliers, bad_words, questions_to_check, logger, scan_drafts
):

    with open(output_file_path, 'w') as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELD_NAMES, dialect='excel')
        writer.writeheader()
        for supplier in suppliers:
            services = get_services(client, supplier["supplierId"], framework_slug, scan_drafts)

            for service in services:
                for key in questions_to_check:
                    if isinstance(service.get(key), str):
                        service_field_values = [service.get(key)]
                    elif isinstance(service.get(key), list):
                        service_field_values = service.get(key)
                    else:
                        service_field_values = []

                    for service_field_value_str in service_field_values:
                        for word in bad_words:
                            if _get_bad_words_in_value(word, service_field_value_str):
                                output_bad_words(
                                    supplier["supplierId"],
                                    framework_slug,
                                    service["id"],
                                    service["serviceName"],
                                    service.get("serviceSummary", service.get("serviceDescription")),
                                    key,
                                    service_field_value_str,
                                    word,
                                    writer,
                                    logger
                                )
                                BAD_WORDS_COUNTER.update({word: 1})


def scan_services_for_bad_words(
    client, bad_words_path, framework_slug, output_dir, content_loader, logger, scan_drafts
):
    bad_words = _get_bad_words_from_file(bad_words_path)
    suppliers = get_suppliers(client, framework_slug)

    output_file_path = '{}/{}-services-with-blacklisted-words.csv'.format(output_dir, framework_slug)

    content_loader.load_metadata(framework_slug, ['service_questions_to_scan_for_bad_words'])
    questions_to_check = content_loader.get_metadata(
        framework_slug, 'service_questions_to_scan_for_bad_words', 'service_questions'
    )

    check_services_with_bad_words(
        output_file_path, framework_slug, client, suppliers, bad_words, questions_to_check, logger, scan_drafts
    )
    return BAD_WORDS_COUNTER
