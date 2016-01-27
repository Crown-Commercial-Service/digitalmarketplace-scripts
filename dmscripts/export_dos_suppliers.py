import os
import sys
from multiprocessing.pool import ThreadPool

from dmapiclient import HTTPError
from dmscripts.insert_dos_framework_results import (
    CORRECT_DECLARATION_RESPONSE_MUST_BE_TRUE, CORRECT_DECLARATION_RESPONSE_MUST_BE_FALSE,
    CORRECT_DECLARATION_RESPONSE_SHOULD_BE_FALSE, MITIGATING_FACTORS,
    CORRECT_DECLARATION_RESPONSES
)

if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv

FRAMEWORK_SLUG = 'digital-outcomes-and-specialists'
DRAFT_STATUSES = [
    'completed',
    'failed',
    'draft',
]
LOTS = [
    'digital-outcomes', 'digital-specialists',
    'user-research-studios', 'user-research-participants',
]


def find_suppliers(client, framework_slug):
    suppliers = client.get_interested_suppliers(framework_slug)['interestedSuppliers']
    return ({'supplier_id': supplier_id} for supplier_id in suppliers)


def add_supplier_info(client):
    def inner(record):
        supplier = client.get_supplier(record['supplier_id'])

        return dict(record,
                    supplier=supplier['suppliers'])

    return inner


def add_framework_info(client, framework_slug):
    def inner(record):
        supplier_framework = client.get_supplier_framework_info(record['supplier']['id'], framework_slug)
        supplier_framework = supplier_framework['frameworkInterest']
        supplier_framework['declaration'] = supplier_framework['declaration'] or {}

        if supplier_framework['declaration'].get('status') != 'complete':
            assert supplier_framework['onFramework'] is False, \
                "Incomplete declaration but not failed, have you inserted the framework result?"

        return dict(record,
                    declaration=supplier_framework['declaration'],
                    onFramework=supplier_framework['onFramework'])

    return inner


def add_draft_counts(client, framework_slug):
    def inner(record):
        counts = {status: {lot: 0 for lot in LOTS} for status in DRAFT_STATUSES}

        for draft in client.find_draft_services_iter(record['supplier']['id'], framework=framework_slug):
            if draft['status'] == 'submitted':
                counts['completed'][draft['lot']] += 1
            elif draft['status'] == 'failed':
                counts['failed'][draft['lot']] += 1
            else:
                counts['draft'][draft['lot']] += 1

        return dict(record, counts=counts)

    return inner


def get_declaration_questions(declaration_content, record):
    for section in declaration_content:
        for question in section.questions:
            yield question, record['declaration'].get(question.id)


def is_incorrect_mandatory_question(question, answer):
    if question.number in CORRECT_DECLARATION_RESPONSE_MUST_BE_TRUE and answer is not True:
        return True
    if question.number in CORRECT_DECLARATION_RESPONSE_MUST_BE_FALSE and answer is not False:
        return True
    if question.number in CORRECT_DECLARATION_RESPONSES:
        if answer not in CORRECT_DECLARATION_RESPONSES[question.number]:
            return True

    return False


def add_failed_questions(declaration_content):
    def inner(record):
        if record['declaration'].get('status') != 'complete':
            return dict(record,
                        failed_mandatory=['INCOMPLETE'],
                        discretionary=[])

        declaration_questions = list(get_declaration_questions(declaration_content, record))

        failed_mandatory = [
            "Q{}".format(question.number)
            for question, answer in declaration_questions
            if is_incorrect_mandatory_question(question, answer)
        ]

        discretionary = [
            ("Q{}".format(question.number), answer)
            for question, answer in declaration_questions
            if question.number in CORRECT_DECLARATION_RESPONSE_SHOULD_BE_FALSE + MITIGATING_FACTORS
        ]

        return dict(record,
                    failed_mandatory=failed_mandatory,
                    discretionary=discretionary)

    return inner


def find_suppliers_with_details(client, content_loader, framework_slug):
    pool = ThreadPool(30)

    content_loader.load_manifest(framework_slug, 'declaration', 'declaration')
    declaration_content = content_loader.get_manifest(framework_slug, 'declaration')

    records = find_suppliers(client, framework_slug)
    records = pool.imap(add_supplier_info(client), records)
    records = pool.imap(add_framework_info(client, framework_slug), records)
    records = pool.imap(add_draft_counts(client, framework_slug), records)
    records = map(add_failed_questions(declaration_content), records)

    return records


def supplier_info(record):
    return [
        ('supplier_name', record['supplier']['name']),
        ('supplier_declaration_name', record['declaration'].get('nameOfOrganisation', '')),
        ('supplier_id', record['supplier']['id']),
        ('trading_name', record['declaration'].get('tradingNames', '')),
        ('registered_address', record['declaration'].get('registeredAddress', '')),
        ('company_number', record['declaration'].get('companyRegistrationNumber', '')),
        ('country_of_registration', record['declaration'].get('currentRegisteredCountry', '')),
    ]


def failed_mandatory_questions(record):
    return [
        ('failed_mandatory', ",".join(question for question in record['failed_mandatory'])),
    ]


def discretionary_questions(record):
    return [
        (question, answer) for question, answer in record['discretionary']
    ]


def contact_details(record):
    return [
        ('contact_name', record['declaration'].get('primaryContact', '')),
        ('contact_email', record['declaration'].get('primaryContactEmail', '')),
    ]


def service_counts(record):
    return [
        ('{}_{}'.format(status, lot), record['counts'][status][lot])
        for status in DRAFT_STATUSES
        for lot in LOTS
    ]


class SuccessfulHandler(object):
    NAME = 'successful'

    def matches(self, record):
        return record['onFramework'] is True

    def create_row(self, record):
        return \
            supplier_info(record) + \
            contact_details(record) + \
            service_counts(record)


class FailedHandler(object):
    NAME = 'failed'

    def matches(self, record):
        return record['onFramework'] is False

    def create_row(self, record):
        return \
            supplier_info(record) + \
            failed_mandatory_questions(record) + \
            contact_details(record) + \
            service_counts(record)


class DiscretionaryHandler(object):
    NAME = 'discretionary'

    def matches(self, record):
        return record['onFramework'] is None

    def create_row(self, record):
        return \
            supplier_info(record) + \
            discretionary_questions(record) + \
            contact_details(record) + \
            service_counts(record)


class MultiCSVWriter(object):
    """Manage writing to multiple CSV files"""
    def __init__(self, output_dir, handlers):
        self.output_dir = output_dir
        self.handlers = handlers
        self._csv_writers = dict()
        self._csv_files = dict()
        self._counters = {
            handler.NAME: 0 for handler in handlers
        }

    def write_row(self, record):
        for handler in self.handlers:
            if handler.matches(record):
                self._counters[handler.NAME] += 1
                row = handler.create_row(record)
                return self.csv_writer(handler, row).writerow(dict(row))
        raise Exception("record not handled by any handler")

    def csv_writer(self, handler, row):
        if handler.NAME not in self._csv_writers:
            fieldnames = [key for key, _ in row]
            self._csv_writers[handler.NAME] = csv.DictWriter(self._csv_files[handler.NAME], fieldnames=fieldnames)
            self._csv_writers[handler.NAME].writeheader()

        return self._csv_writers[handler.NAME]

    def csv_path(self, handler):
        return os.path.join(self.output_dir, handler.NAME + '.csv')

    def __enter__(self):
        for handler in self.handlers:
            self._csv_files[handler.NAME] = open(self.csv_path(handler), 'w+')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for f in self._csv_files.values():
            f.close()

    def print_counts(self):
        print(" ".join("{}={}".format(handler.NAME, self._counters[handler.NAME]) for handler in self.handlers))


def export_suppliers(client, content_loader, output_dir):
    records = find_suppliers_with_details(client, content_loader, FRAMEWORK_SLUG)

    handlers = [SuccessfulHandler(), FailedHandler(), DiscretionaryHandler()]

    with MultiCSVWriter(output_dir, handlers) as writer:
        for i, record in enumerate(records):
            writer.write_row(record)
            if (i + 1) % 100 == 0:
                writer.print_counts()

        writer.print_counts()
        print("DONE")
