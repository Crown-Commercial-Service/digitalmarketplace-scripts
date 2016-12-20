# -*- coding: utf-8 -*-
import jsonschema
import os
import sys
if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv

from multiprocessing.pool import ThreadPool


DRAFT_STATUSES = [
    'completed',
    'failed',
    'draft',
]
LOTS = [
    'digital-outcomes', 'digital-specialists',
    'user-research-studios', 'user-research-participants',
]


def get_validation_errors(candidate, schema):
        validator = jsonschema.Draft4Validator(schema)
        errors = validator.iter_errors(candidate)
        error_keys = [error.path[0] for error in errors]
        return error_keys


def find_suppliers(client, framework_slug):
    suppliers = client.get_interested_suppliers(framework_slug)['interestedSuppliers']
    return ({'supplier_id': supplier_id} for supplier_id in suppliers)


def add_supplier_info(client):
    def inner(record):
        supplier = client.get_supplier(record['supplier_id'])

        return dict(record, supplier=supplier['suppliers'])

    return inner


def add_draft_services(client, framework_slug, lot=None, status=None):
    def inner(record):
        drafts = client.find_draft_services(record["supplier_id"], framework=framework_slug)
        drafts = drafts["services"]

        drafts = [
            draft for draft in drafts
            if (not lot or draft["lotSlug"] == lot) and (not status or draft["status"] == status)
        ]

        return dict(record,
                    services=drafts)

    return inner


def count_field_in_record(field_id, field_label, record):
    return sum(1
               for service in record["services"]
               if field_label in service.get(field_id, []))


def make_field_title(field_id, field_label):
    return "{} {}".format(field_id, field_label)


def make_fields_from_content_question(question, record):
    if question["type"] == "checkboxes":
        for option in question.options:
            # Make a CSV column for each label
            yield (
                make_field_title(question.id, option["label"]),
                count_field_in_record(question.id, option["label"], record)
            )
    elif question.fields:
        for field_id in sorted(question.fields.values()):
            # Make a CSV column containing all values
            yield (
                field_id,
                "|".join(service.get(field_id, "") for service in record["services"])
            )
    else:
        yield (
            question["id"],
            "|".join(str(service.get(question["id"], "")) for service in record["services"])
        )


def add_framework_info(client, framework_slug):
    def inner(record):
        supplier_framework = client.get_supplier_framework_info(record['supplier_id'], framework_slug)
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


def add_failed_questions(declaration_content,
                         declaration_definite_pass_schema,
                         declaration_baseline_schema
                         ):
    def inner(record):
        if record['declaration'].get('status') != 'complete':
            return dict(record,
                        failed_mandatory=['INCOMPLETE'],
                        discretionary=[])

        declaration_questions = list(get_declaration_questions(declaration_content, record))

        all_failed_keys = get_validation_errors(record['declaration'], declaration_definite_pass_schema)

        if declaration_baseline_schema:
            baseline_only_failed_keys = get_validation_errors(record['declaration'], declaration_baseline_schema)
        else:
            baseline_only_failed_keys = all_failed_keys

        failed_mandatory = [
            "Q{}".format(question.number)
            for question, answer in declaration_questions
            if question.id in baseline_only_failed_keys
            ]
        discretionary = [
            ("Q{}".format(question.number), answer)
            for question, answer in declaration_questions
            if question.id in all_failed_keys and question.id not in baseline_only_failed_keys
        ]

        return dict(record,
                    failed_mandatory=failed_mandatory,
                    discretionary=discretionary)

    return inner


def find_suppliers_with_details(client,
                                content_loader,
                                framework_slug,
                                declaration_definite_pass_schema,
                                declaration_baseline_schema
                                ):
    pool = ThreadPool(30)

    content_loader.load_manifest(framework_slug, 'declaration', 'declaration')
    declaration_content = content_loader.get_manifest(framework_slug, 'declaration')

    records = find_suppliers(client, framework_slug)
    records = pool.imap(add_supplier_info(client), records)
    records = pool.imap(add_framework_info(client, framework_slug), records)
    records = pool.imap(add_draft_counts(client, framework_slug), records)
    records = map(add_failed_questions(declaration_content,
                                       declaration_definite_pass_schema,
                                       declaration_baseline_schema), records)

    return records


def supplier_info(record):
    return [
        ('supplier_name', record['supplier']['name']),
        ('supplier_declaration_name', record['declaration'].get('nameOfOrganisation', '')),
        ('supplier_id', record['supplier']['id']),
        ('trading_name', record['declaration'].get('tradingNames', '')),
        ('trading_status', record['declaration'].get('tradingStatus', '')),
        ('registered_address_building', record['declaration'].get('registeredAddressBuilding', '')),
        ('registered_address_town', record['declaration'].get('registeredAddressTown', '')),
        ('registered_address_postcode', record['declaration'].get('registeredAddressPostcode', '')),
        ('duns_number', record['supplier'].get('dunsNumber', '')),
        ('company_number', record['declaration'].get('companyRegistrationNumber', '')),
        ('country_of_registration', record['declaration'].get('currentRegisteredCountry', '')),
        ('vat_number', record['declaration'].get('registeredVATNumber', '')),
        ('size', record['declaration'].get('organisationSize', '')),
        ('subcontracting', record['declaration'].get('subcontracting', '')),
    ]


def failed_mandatory_questions(record):
    return [
        ('failed_mandatory', ",".join(question for question in record['failed_mandatory'])),
    ]


def discretionary_questions(record):
    failed_questions = [("failed_discretionary", record['discretionary'])]
    mitigating_factors = [
        ("MITIGATING 1", record['declaration'].get('mitigatingFactors', '')),
        ("MITIGATING 2", record['declaration'].get('mitigatingFactors2', ''))
    ]
    return failed_questions + mitigating_factors


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


def write_csv(records, make_row, filename):
    """Write a list of records out to CSV"""
    def fieldnames(row):
        return [field[0] for field in row]

    writer = None

    with open(filename, "w+") as f:
        for record in records:
            sys.stdout.write(".")
            sys.stdout.flush()
            row = make_row(record)
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=fieldnames(row))
                writer.writeheader()
            writer.writerow(dict(row))


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


def export_suppliers(
        client,
        framework_slug,
        content_loader,
        output_dir,
        declaration_definite_pass_schema,
        declaration_baseline_schema=None
):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    records = find_suppliers_with_details(client,
                                          content_loader,
                                          framework_slug,
                                          declaration_definite_pass_schema,
                                          declaration_baseline_schema
                                          )

    handlers = [SuccessfulHandler(), FailedHandler(), DiscretionaryHandler()]

    with MultiCSVWriter(output_dir, handlers) as writer:
        for i, record in enumerate(records):
            writer.write_row(record)
            if (i + 1) % 100 == 0:
                writer.print_counts()

        writer.print_counts()
        print("DONE")
