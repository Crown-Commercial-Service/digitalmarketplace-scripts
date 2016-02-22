import os
import sys

if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv


NEW_LOT_FIELDS = ["completed_lots_{}".format(idx) for idx in range(1, 5)]
IMPORT_DATA_CONFIG = {
    'digital-outcomes-and-specialists': {
        'lot_fields': [
            'completed_digital-outcomes',
            'completed_digital-specialists',
            'completed_user-research-studios',
            'completed_user-research-participants',
        ],
        'lot_names': [
            'Digital outcomes',
            'Digital specialists',
            'User research studios',
            'User research participants',
        ],
        'framework_agreement': {
            'required_fields': [
                'supplier_id',
                'trading_name',
                'registered_address',
                'company_number',
            ]
        },
        'result_letter': {
            'required_fields': [
                'supplier_id',
                'supplier_declaration_name'
            ]
        }
    },
}


def fill_list_based_on_flags(list_of_flags, potential_values):
    new_list = []
    for idx, flag in enumerate(list_of_flags):
        if bool(int(flag)):
            new_list.append(potential_values[idx])
    if len(new_list) < len(potential_values):
        # pad out array
        new_list.extend(
            ['' for entry in range(len(potential_values) - len(new_list))]
        )
    return new_list


def get_new_field_names(required_fields):
    field_names = required_fields
    field_names.extend(NEW_LOT_FIELDS)
    return field_names


def reformat_csv_data(csv_data, framework_slug, document_type):
    config = IMPORT_DATA_CONFIG[framework_slug]
    required_fields = config[document_type]['required_fields']
    import_data = []

    for idx, row in enumerate(csv_data):
        # get the cells for the required columns
        new_row = {field_name: row[field_name] for field_name in required_fields}
        # add completed lots
        lot_results = fill_list_based_on_flags(
            [row[lot_field] for lot_field in config['lot_fields']], config['lot_names'])
        new_row.update(
            {NEW_LOT_FIELDS[idx]: lot_results[idx] for idx in range(0, len(lot_results))})
        import_data.append(new_row)

    return import_data


def get_list_from_csv_file(csvfile):
    csv_reader = csv.DictReader(csvfile)
    return [row for row in csv_reader]


def create_import_data_file_for_documents(import_data, target_dir, framework_slug, document_type):
    new_field_names = get_new_field_names(
        IMPORT_DATA_CONFIG[framework_slug][document_type]['required_fields'])
    file_path = os.path.join(target_dir, '{}_import_data.txt'.format(document_type))
    csv_writer = csv.DictWriter(open(file_path, 'w+'), fieldnames=new_field_names, delimiter="\t", lineterminator="\n")
    csv_writer.writeheader()
    for row in import_data:
        csv_writer.writerow(row)


def generate_import_data(suppliers_file_path, import_data_dir_path, framework_slug, document_type):
    with open(suppliers_file_path) as suppliers_file:
        suppliers_csv_data = get_list_from_csv_file(suppliers_file)
    suppliers_data = reformat_csv_data(suppliers_csv_data, framework_slug, document_type)
    create_import_data_file_for_documents(suppliers_data, import_data_dir_path, framework_slug, document_type)
