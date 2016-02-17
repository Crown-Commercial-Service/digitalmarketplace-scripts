import pytest
import os
import tempfile
import shutil

from dmscripts.generate_dos_import_data import (
    get_list_from_csv_file, fill_list_based_on_flags, reformat_csv_data,
    get_lot_results, get_indices_of_required_columns, create_import_data_file_for_documents,
    reduce_row_to_list)


CSV_FILE_LIST = [
    ["supplier_name", "supplier_declaration_name", "supplier_id", "trading_name", "registered_address", "company_number", "country_of_registration", "contact_name", "contact_email", "completed_digital-outcomes", "completed_digital-specialists", "completed_user-research-studios", "completed_user-research-participants", "failed_digital-outcomes", "failed_digital-specialists", "failed_user-research-studios", "failed_user-research-participants", "draft_digital-outcomes", "draft_digital-specialists", "draft_user-research-studios", "draft_user-research-participants"],  # noqa
    ["CloudTech Limited", "CloudTech limited", "12345", "CloudTech Limited", "21 Fenchurch Street, London, EC3M 3BY", "123456789", "United Kingdom", "Brian Church", "brian.church@cloudtech.com", "1", "1", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],  # noqa
    ["Human Research Systems Limited", "Human Research Systems limited", "67890", "Human Research Systems Limited", "45 Clerkenwell Road, London, EC1R 5BL", "987654321", "United Kingdom", "Kevin Briggs", "kevin.briggs@hrs.com", "0", "0", "1", "1", "0", "0", "0", "0", "0", "0", "0", "0"],  # noqa
    ["Total Web Limited", "Total Web limited", "66789", "Total Web Limited", "33 Fore Street, London, EC2Y 5EJ", "678901234", "United Kingdom", "Sue Watson", "sue.watch@totalweb.com", "1", "1", "0", "0", "0", "0", "0", "0", "0", "0", "1", "1"]  # noqa
]

FRAMEWORK_AGREEMENT_IMPORT_DATA_LIST = [
    ["trading_name", "registered_address", "company_number", "completed_lots_1", "completed_lots_2", "completed_lots_3", "completed_lots_4"],  # noqa
    ["CloudTech Limited", "21 Fenchurch Street, London, EC3M 3BY", "123456789", "Digital outcomes", "Digital specialists", "", ""],  # noqa
    ["Human Research Systems Limited", "45 Clerkenwell Road, London, EC1R 5BL", "987654321", "User research studios", "User research participants", "", ""],  # noqa
    ["Total Web Limited", "33 Fore Street, London, EC2Y 5EJ", "678901234", "Digital outcomes", "Digital specialists", "", ""]  # noqa
]

RESULT_LETTER_IMPORT_DATA_LIST = [
    ["supplier_id", "supplier_declaration_name", "completed_lots_1", "completed_lots_2", "completed_lots_3", "completed_lots_4"],  # noqa
    ["12345", "CloudTech limited",  "Digital outcomes", "Digital specialists", "", ""],  # noqa
    ["67890", "Human Research Systems limited", "User research studios", "User research participants", "", ""],  # noqa
    ["66789", "Total Web limited", "Digital outcomes", "Digital specialists", "", ""]  # noqa
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


def test_reduce_row_to_list_with_linear_sequence():
    assert reduce_row_to_list([
        "CloudTech Limited", "CloudTech limited", "12345",
        "CloudTech Limited", "21 Fenchurch Street, London, EC3M 3BY"
    ], [0, 1, 2, 3]) == [
        "CloudTech Limited", "CloudTech limited", "12345",
        "CloudTech Limited"
    ]


def test_reduce_row_to_list_with_varied_sequence():
    assert reduce_row_to_list([
        "CloudTech Limited", "CloudTech limited", "12345",
        "CloudTech Limited", "21 Fenchurch Street, London, EC3M 3BY"
    ], [0, 2, 4]) == [
        "CloudTech Limited", "12345",
        "21 Fenchurch Street, London, EC3M 3BY"
    ]


def test_get_lot_results_for_supplier_with_only_completed_lots():
    assert get_lot_results(
        CSV_FILE_LIST[1][len(CSV_FILE_LIST[1]) - 12:],
        [
            "Digital outcomes",
            "Digital specialists",
            "User research studios",
            "User research participants",
        ]) == {
        "completed": [
            "Digital outcomes",
            "Digital specialists",
            "",
            ""
        ],
        "failed": ["", "", "", ""],
        "draft": ["", "", "", ""]
    }


def test_get_lot_results_for_supplier_with_different_lots():
    assert get_lot_results(
        CSV_FILE_LIST[3][len(CSV_FILE_LIST[3]) - 12:],
        [
            "Digital outcomes",
            "Digital specialists",
            "User research studios",
            "User research participants",
        ]) == {
        "completed": [
            "Digital outcomes",
            "Digital specialists",
            "",
            ""
        ],
        "failed": ["", "", "", ""],
        "draft": [
            "User research studios",
            "User research participants",
            "",
            ""
        ]
    }


def test_get_indices_of_required_columns():
    assert get_indices_of_required_columns(
        CSV_FILE_LIST[0],
        [
            "supplier_name", "supplier_id", "company_number",
        ]
    ) == [0, 2, 5]


def test_get_indices_of_required_columns_if_non_required():
    assert get_indices_of_required_columns(
        CSV_FILE_LIST[0],
        []
    ) == []


def test_reformat_csv_data_for_framework_agreement():
    assert reformat_csv_data(
        CSV_FILE_LIST, 'digital-outcomes-and-specialists', 'framework_agreement'
    ) == FRAMEWORK_AGREEMENT_IMPORT_DATA_LIST


def test_reformat_csv_data_for_framework_agreement():
    assert reformat_csv_data(
        CSV_FILE_LIST, 'digital-outcomes-and-specialists', 'result_letter'
    ) == RESULT_LETTER_IMPORT_DATA_LIST


def test_create_import_data_file_for_supplier_for_framework_agreement():
    dir_path = tempfile.mkdtemp()
    create_import_data_file_for_documents(
        FRAMEWORK_AGREEMENT_IMPORT_DATA_LIST,
        dir_path,
        'framework_agreement'
    )
    example_import_data_file = open('tests/fixtures/example-dos-framework-agreement-import-data.txt')
    created_file_path = os.path.join(dir_path, 'framework_agreement_import_data.txt')
    assert os.path.isfile(created_file_path)
    created_file = open(created_file_path)
    example_import_data_file_contents = example_import_data_file.read()
    created_file_contents = created_file.read()

    created_file.close()
    example_import_data_file.close()
    shutil.rmtree(dir_path)

    assert example_import_data_file_contents == created_file_contents


def test_create_import_data_file_for_supplier_for_result_letter():
    dir_path = tempfile.mkdtemp()
    create_import_data_file_for_documents(
        RESULT_LETTER_IMPORT_DATA_LIST,
        dir_path,
        'result_letter'
    )
    example_import_data_file = open('tests/fixtures/example-dos-result-letter-import-data.txt')
    created_file_path = os.path.join(dir_path, 'result_letter_import_data.txt')
    assert os.path.isfile(created_file_path)
    created_file = open(created_file_path)
    example_import_data_file_contents = example_import_data_file.read()
    created_file_contents = created_file.read()

    created_file.close()
    example_import_data_file.close()
    shutil.rmtree(dir_path)

    assert example_import_data_file_contents == created_file_contents
