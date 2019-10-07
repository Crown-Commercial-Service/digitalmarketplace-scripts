import os


def csv_path(output_dir, _filename):
    return os.path.join(output_dir, '{}.csv'.format(_filename))


def export_data_to_csv(output_dir, config, data, logger):
    # write up your CSV
    filename = csv_path(output_dir, config['name'])
    try:
        data.to_csv(filename, index=False, encoding='utf-8')
        logger.info('Printed `{}` with {} rows'.format(filename, len(data)))
    except AttributeError as exc:
        logger.error(f"Unable to write to CSV for {filename}: {exc}")
