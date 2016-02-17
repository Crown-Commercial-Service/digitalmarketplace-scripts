import os
import sys

if sys.version_info[0] < 3:
    import unicodecsv as csv
else:
    import csv


IMPORT_DATA_CONFIG = {
    'digital-outcomes-and-specialists': {
        'lot_names': [
            'Digital outcomes',
            'Digital specialists',
            'User research studios',
            'User research participants',
        ],
        'framework_agreement': {
            'required_columns': [
                'supplier_id',
                'trading_name',
                'registered_address',
                'company_number',
            ]
        },
        'result_letter': {
            'required_columns': [
                'supplier_id',
                'supplier_declaration_name'
            ]
        }
    },
}


def reduce_row_to_list(row, selected_indices):
    result = []
    lastIdx = len(row) - 1
    for idx in selected_indices:
        if idx <= lastIdx:
            result.append(row[idx])
    return result


def get_required_column_indices(column_headings, required_column_headings):
    return [column_headings.index(heading) for heading in required_column_headings]


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


def get_lot_results(values, lot_names):
    # results are last 3 blocks of 4
    number_of_lots = len(lot_names)
    results_by_lot = {
        'completed': values[:number_of_lots],
        'failed': values[number_of_lots:(number_of_lots * 2)],
        'draft': values[(number_of_lots * 2):(number_of_lots * 3)],
    }
    for status in results_by_lot:
        results_by_lot[status] = fill_list_based_on_flags(results_by_lot[status], lot_names)
    return results_by_lot


def get_indices_of_required_columns(supplier_info_headings, required_columns):
    return [supplier_info_headings.index(heading) for heading in required_columns]


def reformat_csv_data(csv_data, framework_slug, document_type):
    config = IMPORT_DATA_CONFIG[framework_slug]
    number_of_lots = len(config['lot_names'])
    lot_results_start_idx = len(csv_data[1]) - (3 * number_of_lots)
    supplier_info_headings = csv_data[0][:lot_results_start_idx]
    required_column_indicies = get_indices_of_required_columns(
        supplier_info_headings, config[document_type]['required_columns'])

    import_data = []

    # start column headings with supplier info
    import_data.append(
        reduce_row_to_list(supplier_info_headings, required_column_indicies))
    # add new headings for completed lots
    import_data[0].extend(['completed_lots_{}'.format(idx) for idx in range(1, 5)])

    for idx, row in enumerate(csv_data):
        if idx > 0:
            # get all values except those for the lot results
            supplier_info_values = row[:lot_results_start_idx]
            import_data.append(reduce_row_to_list(supplier_info_values, required_column_indicies))
            # add completed lots
            lot_results = get_lot_results(
                csv_data[idx][lot_results_start_idx:], config['lot_names'])
            import_data[idx].extend(lot_results['completed'])

    return import_data


def get_list_from_csv_file(csvfile):
    csv_reader = csv.reader(csvfile)
    return [row for row in csv_reader]


def create_import_data_file_for_documents(import_data, target_dir, document_type):
    file_path = os.path.join(target_dir, '{}_import_data.txt'.format(document_type))
    csv_writer = csv.writer(open(file_path, 'w+'), delimiter="\t", lineterminator="\n")
    for row in import_data:
        csv_writer.writerow(row)


def generate_import_data(suppliers_file_path, import_data_dir_path, framework_slug, document_type):
    with open(suppliers_file_path) as suppliers_file:
        suppliers_csv_data = get_list_from_csv_file(suppliers_file)
    suppliers_data = reformat_csv_data(suppliers_csv_data, framework_slug, document_type)
    create_import_data_file_for_documents(suppliers_data, import_data_dir_path, document_type)
