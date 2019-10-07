from datetime import datetime
from dmutils.formats import DATE_FORMAT, DATETIME_FORMAT
from dmscripts.models import queries


def format_datetime_string_as_date(dt):
    return datetime.strptime(dt, DATETIME_FORMAT).strftime(DATE_FORMAT) if dt else None


def remove_username_from_email_address(ea):
    return '{}'.format(ea.split('@').pop()) if ea else None


def construct_brief_url(brief_id):
    return (
        'https://www.digitalmarketplace.service.gov.uk/'
        'digital-outcomes-and-specialists/opportunities/{}'.format(brief_id)
    )


def extract_id_from_user_info(user_data):
    return ','.join([str(user['id']) for user in user_data])


def query_data_from_config(config, logger, limit, client, output_dir):
    data = {}
    if 'base_model' in config:
        required_keys = list(config['keys']) + list(config.get('assign_json_subfields', {}).keys())
        data = queries.base_model(config['base_model'], required_keys, config['get_data_kwargs'],
                                  client=client, logger=logger, limit=limit)

    elif 'model' in config:
        try:
            data = queries.model(config['model'], directory=output_dir)
        except FileNotFoundError as exc:
            # Some reports rely on a previous model's CSV being present - skip if it's not there
            logger.error(f"{exc}, skipping report for {config['name']}")
            return None

    if 'joins' in config:
        for join in config['joins']:
            data = queries.join(data, directory=output_dir, **join)

    if 'get_by_model_fk' in config:
        data = queries.get_by_model_fk(
            config['get_by_model_fk'],
            config['keys'],
            data,
            client
        )

    # transform values that we want to transform
    if 'assign_json_subfields' in config:
        for field, subfields in config['assign_json_subfields'].items():
            data = queries.assign_json_subfields(field, subfields, data)

    # TODO: figure out if this is still needed
    if 'duplicate_fields' in config:
        for field, new_name in config['duplicate_fields']:
            data = queries.duplicate_fields(data, field, new_name)

    if 'process_fields' in config:
        data = queries.process_fields(config['process_fields'], data)

    if 'add_counts' in config:
        data = queries.add_counts(data=data, directory=output_dir, **config['add_counts'])

    if 'aggregation_counts' in config:
        for count in config['aggregation_counts']:
            data = queries.add_aggregation_counts(data=data, **count)

    if 'filter_query' in config:
        # filter out things we don't want
        data = queries.filter_rows(config['filter_query'], data)
        logger.info(
            '{} {} remaining after filtering'.format(len(data), config['name'])
        )

    if 'group_by' in config:
        data = queries.group_by(config['group_by'], data)

    # Only keep requested keys in the output CSV
    keys = [
        j for j in (
            ".".join(str(part) for part in k) if isinstance(k, (tuple, list)) else k
            for k in config['keys']
        ) if j in data
    ]
    data = data[keys]

    if 'rename_fields' in config:
        data = queries.rename_fields(config['rename_fields'], data)

    # sort list by some dict value
    if 'sort_by' in config:
        data = queries.sort_by(config['sort_by'], data)

    # TODO: figure out if this is still needed
    if 'drop_duplicates' in config and config['drop_duplicates']:
        data = queries.drop_duplicates(data)

    return data
