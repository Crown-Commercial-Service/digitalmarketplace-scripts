import pytest
import os
import tempfile
import shutil

from dmscripts.generate_pdf_import_data import (
    get_list_from_csv_file, fill_list_based_on_flags, filter_csv_data,
    create_import_data_file_for_documents, get_new_field_names)


CSV_FILE_LIST = [
    {"supplier_name": "CloudTech Limited", "supplier_declaration_name": "CloudTech limited", "supplier_id": "12345", "trading_name": "CloudTech Limited", "registered_address": "21 Fenchurch Street, London, EC3M 3BY", "company_number": "123456789", "country_of_registration": "United Kingdom", "contact_name": "Brian Church", "contact_email": "brian.church@cloudtech.com", "completed_digital-outcomes": "1", "completed_digital-specialists": "1", "completed_user-research-studios": "0", "completed_user-research-participants": "0", "failed_digital-outcomes": "0", "failed_digital-specialists": "0", "failed_user-research-studios": "0", "failed_user-research-participants": "0", "draft_digital-outcomes": "0", "draft_digital-specialists": "0", "draft_user-research-studios": "0", "draft_user-research-participants": "0"},  # noqa
    {"supplier_name": "Human Research Systems Limited", "supplier_declaration_name": "Human Research Systems limited", "supplier_id": "67890", "trading_name": "Human Research Systems Limited", "registered_address": "45 Clerkenwell Road, London, EC1R 5BL", "company_number": "987654321", "country_of_registration": "United Kingdom", "contact_name": "Kevin Briggs", "contact_email": "kevin.briggs@hrs.com", "completed_digital-outcomes": "0", "completed_digital-specialists": "0", "completed_user-research-studios": "1", "completed_user-research-participants": "1", "failed_digital-outcomes": "0", "failed_digital-specialists": "0", "failed_user-research-studios": "0", "failed_user-research-participants": "0", "draft_digital-outcomes": "0", "draft_digital-specialists": "0", "draft_user-research-studios": "0", "draft_user-research-participants": "0"},  # noqa
    {"supplier_name": "Total Web Limited", "supplier_declaration_name": "Total Web limited", "supplier_id": "66789", "trading_name": "Total Web Limited", "registered_address": "33 Fore Street, London, EC2Y 5EJ", "company_number": "678901234", "country_of_registration": "United Kingdom", "contact_name": "Sue Watson", "contact_email": "sue.watch@totalweb.com", "completed_digital-outcomes": "1", "completed_digital-specialists": "1", "completed_user-research-studios": "0", "completed_user-research-participants": "0", "failed_digital-outcomes": "0", "failed_digital-specialists": "0", "failed_user-research-studios": "0", "failed_user-research-participants": "0", "draft_digital-outcomes": "0", "draft_digital-specialists": "0", "draft_user-research-studios": "1", "draft_user-research-participants": "1"}  # noqa
]

FRAMEWORK_AGREEMENT_IMPORT_DATA_LIST = [
    {"supplier_id": "12345", "trading_name": "CloudTech Limited", "registered_address": "21 Fenchurch Street, London, EC3M 3BY", "company_number": "123456789", "completed_lots_1": "Digital outcomes", "completed_lots_2": "Digital specialists", "completed_lots_3": "", "completed_lots_4": ""},  # noqa
    {"supplier_id": "67890", "trading_name": "Human Research Systems Limited", "registered_address": "45 Clerkenwell Road, London, EC1R 5BL", "company_number": "987654321", "completed_lots_1": "User research studios", "completed_lots_2": "User research participants", "completed_lots_3": "", "completed_lots_4": ""},  # noqa
    {"supplier_id": "66789", "trading_name": "Total Web Limited", "registered_address": "33 Fore Street, London, EC2Y 5EJ", "company_number": "678901234", "completed_lots_1": "Digital outcomes", "completed_lots_2": "Digital specialists", "completed_lots_3": "", "completed_lots_4": ""}  # noqa
]

RESULT_LETTER_IMPORT_DATA_LIST = [
    {"supplier_id": "12345", "supplier_declaration_name": "CloudTech limited", "completed_lots_1": "Digital outcomes", "completed_lots_2": "Digital specialists", "completed_lots_3": "", "completed_lots_4": ""},  # noqa
    {"supplier_id": "67890", "supplier_declaration_name": "Human Research Systems limited", "completed_lots_1": "User research studios", "completed_lots_2": "User research participants", "completed_lots_3": "", "completed_lots_4": ""},  # noqa
    {"supplier_id": "66789", "supplier_declaration_name": "Total Web limited", "completed_lots_1": "Digital outcomes", "completed_lots_2": "Digital specialists", "completed_lots_3": "", "completed_lots_4": ""}  # noqa
]


def test_get_list_from_csv_file():
    csv_file = open('tests/fixtures/example-dos-suppliers.csv')
    assert get_list_from_csv_file(csv_file) == CSV_FILE_LIST


def test_fill_list_based_on_flags_for_linear_sequence():
    assert fill_list_based_on_flags(
        ["0", "0", "1", "1"],
        [
            "digital-outcomes", "digital-specialists",
            "user-research-studios", "user-research-participants",
        ]
    ) == ["user-research-studios", "user-research-participants", "", ""]


def test_fill_list_based_on_flags_for_varied_sequence():
    assert fill_list_based_on_flags(
        ["1", "0", "1", "0"],
        [
            "digital-outcomes", "digital-specialists",
            "user-research-studios", "user-research-participants",
        ]
    ) == ["digital-outcomes", "user-research-studios", "", ""]


def test_get_new_field_names():
    assert get_new_field_names([
        'supplier_id',
        'trading_name',
    ]) == [
        'supplier_id',
        'trading_name',
        'completed_lots_1',
        'completed_lots_2',
        'completed_lots_3',
        'completed_lots_4',
    ]


def test_filter_csv_data_for_framework_agreement():
    assert filter_csv_data(
        CSV_FILE_LIST, 'digital-outcomes-and-specialists', 'framework_agreement'
    ) == FRAMEWORK_AGREEMENT_IMPORT_DATA_LIST


def test_filter_csv_data_for_framework_agreement():
    assert filter_csv_data(
        CSV_FILE_LIST, 'digital-outcomes-and-specialists', 'result_letter'
    ) == RESULT_LETTER_IMPORT_DATA_LIST


def test_create_import_data_file_for_supplier_for_framework_agreement():
    dir_path = tempfile.mkdtemp()
    create_import_data_file_for_documents(
        FRAMEWORK_AGREEMENT_IMPORT_DATA_LIST,
        dir_path,
        'digital-outcomes-and-specialists',
        'framework_agreement'
    )
    with open('tests/fixtures/example-dos-framework-agreement-import-data.txt') as example_import_data_file:  # noqa
        created_file_path = os.path.join(dir_path, 'framework_agreement_import_data.txt')
        try:
            assert os.path.isfile(created_file_path)
            with open(created_file_path) as created_file:
                example_import_data_file_contents = example_import_data_file.read()
                created_file_contents = created_file.read()

                assert example_import_data_file_contents == created_file_contents
        finally:
            shutil.rmtree(dir_path)


def test_create_import_data_file_for_supplier_for_result_letter():
    dir_path = tempfile.mkdtemp()
    create_import_data_file_for_documents(
        RESULT_LETTER_IMPORT_DATA_LIST,
        dir_path,
        'digital-outcomes-and-specialists',
        'result_letter'
    )
    with open('tests/fixtures/example-dos-result-letter-import-data.txt') as example_import_data_file:  # noqa
        created_file_path = os.path.join(dir_path, 'result_letter_import_data.txt')
        try:
            assert os.path.isfile(created_file_path)
            with open(created_file_path) as created_file:
                example_import_data_file_contents = example_import_data_file.read()
                created_file_contents = created_file.read()

                assert example_import_data_file_contents == created_file_contents
        finally:
            shutil.rmtree(dir_path)
