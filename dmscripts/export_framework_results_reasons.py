# -*- coding: utf-8 -*-
from collections import OrderedDict
from itertools import chain
import jsonschema
import os

from dmscripts.helpers.csv_helpers import MultiCSVWriter
from dmscripts.helpers.framework_helpers import find_suppliers_with_details_and_draft_service_counts


DRAFT_STATUSES = [
    'completed',
    'failed',
    'draft',
]


def get_validation_errors(candidate, schema):
    validator = jsonschema.Draft4Validator(schema)
    errors = validator.iter_errors(candidate)
    error_keys = [error.path[0] for error in errors]
    return error_keys


def add_failed_questions(questions_numbers,
                         declaration_definite_pass_schema,
                         declaration_discretionary_pass_schema
                         ):
    def inner(record):
        if record['declaration'].get('status') != 'complete':
            return dict(record,
                        failed_mandatory=['INCOMPLETE'],
                        discretionary=[])

        all_failed_keys = get_validation_errors(record['declaration'], declaration_definite_pass_schema)

        if declaration_discretionary_pass_schema:
            baseline_only_failed_keys = get_validation_errors(
                record['declaration'],
                declaration_discretionary_pass_schema
            )
        else:
            baseline_only_failed_keys = all_failed_keys

        failed_mandatory = [
            "Q{} - {}".format(question_number, question_id)
            for question_id, question_number in questions_numbers.items()
            if question_id in baseline_only_failed_keys
        ]
        discretionary = [
            ("Q{} - {}".format(question_number, question_id), record['declaration'].get(question_id, ""))
            for question_id, question_number in questions_numbers.items()
            if question_id in all_failed_keys and question_id not in baseline_only_failed_keys
        ]

        return dict(record,
                    failed_mandatory=failed_mandatory,
                    discretionary=discretionary)

    return inner


def find_suppliers_with_details(client,
                                questions_numbers,
                                framework_slug,
                                declaration_definite_pass_schema,
                                declaration_discretionary_pass_schema,
                                supplier_ids=None,
                                map_impl=map,
                                ):
    records = find_suppliers_with_details_and_draft_service_counts(
        client,
        framework_slug,
        supplier_ids,
        map_impl=map_impl,
    )
    records = list(map(add_failed_questions(questions_numbers,
                                            declaration_definite_pass_schema,
                                            declaration_discretionary_pass_schema), records))

    return records


def supplier_info(record):
    return [
        ('supplier_name', record['supplier']['name']),
        ('supplier_id', record['supplier']['id']),
    ]


def failed_mandatory_questions(record):
    return [
        ('failed_mandatory', ",".join(question for question in record['failed_mandatory'])),
    ]


def discretionary_questions(record):
    failed_questions = [("failed_discretionary", record['discretionary'])]
    mitigating_factors = [
        ("mitigating factors 1", record['declaration'].get('mitigatingFactors', '')),
        ("mitigating factors 2", record['declaration'].get('mitigatingFactors2', ''))
    ]
    return failed_questions + mitigating_factors


def contact_details(record):
    return [
        ('contact_name', record['declaration'].get('primaryContact', '')),
        ('contact_email', record['declaration'].get('primaryContactEmail', '')),
    ]


class SuccessfulHandler(object):
    NAME = 'successful'

    def matches(self, record):
        return record['onFramework'] is True

    def should_write(self, record):
        return True

    def create_row(self, record):
        return \
            supplier_info(record) + \
            contact_details(record)


class FailedHandler(object):
    NAME = 'failed'

    def matches(self, record):
        return record['onFramework'] is False

    def should_write(self, record):
        # Only include failed complete applications, not people who didn't make an application
        if record.get('failed_mandatory') and 'INCOMPLETE' in record.get('failed_mandatory'):
            return False
        draft_counts = record.get('counts')
        # Keys in the Counter are tuples such as ('digital-specialists', 'submitted') so count[1] will match the status
        # Failed services are also "submitted" and "complete" so count these too
        completed_count = sum(
            draft_counts[key] for key in
            [count for count in draft_counts if count[1] in ['submitted', 'failed']]
        )
        if completed_count == 0:
            return False
        if not record.get('failed_mandatory'):
            record['failed_mandatory'] = ['No passed lot']
        return True

    def create_row(self, record):
        return \
            supplier_info(record) + \
            failed_mandatory_questions(record) + \
            contact_details(record)


class DiscretionaryHandler(object):
    NAME = 'discretionary'

    def matches(self, record):
        return record['onFramework'] is None

    def should_write(self, record):
        return True

    def create_row(self, record):
        return \
            supplier_info(record) + \
            discretionary_questions(record) + \
            contact_details(record)


def get_questions_numbers_from_framework(framework_slug, content_loader):
    content_loader.load_manifest(framework_slug, 'declaration', 'declaration')
    return OrderedDict(
        (question.id, question.number,)
        for question in sorted(chain.from_iterable(
            section.questions for section in content_loader.get_manifest(framework_slug, 'declaration').sections
        ), key=lambda question: question.number)
    )


def export_suppliers(
    client,
    framework_slug,
    content_loader,
    output_dir,
    declaration_definite_pass_schema,
    declaration_discretionary_pass_schema=None,
    supplier_ids=None,
    map_impl=map,
):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    questions_numbers = get_questions_numbers_from_framework(framework_slug, content_loader)

    records = find_suppliers_with_details(
        client,
        questions_numbers,
        framework_slug,
        declaration_definite_pass_schema,
        declaration_discretionary_pass_schema,
        supplier_ids,
        map_impl=map_impl,
    )

    handlers = [SuccessfulHandler(), FailedHandler(), DiscretionaryHandler()]

    with MultiCSVWriter(output_dir, handlers) as writer:
        for i, record in enumerate(records):
            writer.write_row(record)
            if (i + 1) % 100 == 0:
                writer.print_counts()

        writer.print_counts()
        print("DONE")
