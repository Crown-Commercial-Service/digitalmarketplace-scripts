import pandas

from dmscripts.models.writecsv import csv_path
from dmscripts.models.modeltrawler import ModelTrawler


def base_model(base_model, keys, get_data_kwargs, client, logger=None, limit=None):
    mt = ModelTrawler(base_model, client)

    data = list(mt.get_data(keys=keys, limit=limit, **get_data_kwargs))
    logger.info(
        '{} {} returned after {}s'.format(len(data), base_model, mt.get_time_running())
    )

    return pandas.DataFrame(data)


def model(model, directory):
    return pandas.read_csv(csv_path(directory, model))


def join(join, directory):
    models = [model['model'] for model in join]
    data, joined = (pandas.read_csv(csv_path(directory, model)) for model in models)
    left_on, right_on = (model['key'] for model in join)

    return data.merge(joined, left_on=left_on, right_on=right_on,
                      suffixes=['_{}'.format(model) for model in models])


def filter_rows(filter_query, data):
    if not filter_query:
        return data

    return data.query(filter_query)


def process_fields(rules, data):
    for field, fn in rules.items():
        data[field] = data[field].apply(fn)

    return data


def rename_fields(columns, data):
    """ Replace any column names using a dict of 'old column name': 'new column name' """
    return data.rename(columns=columns)


def sort_by(columns, data):
    return data.sort_values(by=columns)


def add_counts(join, group_by, model, data, directory):
    left_on, right_on = join
    count_data = pandas.read_csv(csv_path(directory, model)).groupby(
        [right_on, group_by]
    ).size().reset_index(name='_count')

    for group in count_data[group_by].unique():
        data["{}-{}".format(group_by, group)] = data.merge(
            count_data[count_data[group_by] == group],
            left_on=left_on, right_on=right_on, how='left'
        )['_count'].fillna(0)

    return data


def add_aggregation_counts(data, group_by, join, count_name, query=None):
    left_on, right_on = join

    count_data = (data.query(query) if query else data).groupby(group_by)[group_by].count()
    count_data_frame = pandas.DataFrame({group_by: count_data.index, count_name: count_data})
    data = data.merge(count_data_frame, how='left', left_on=left_on, right_on=right_on)

    return data


def assign_json_subfields(field, subfields, data):
    """Apply subfields from field to data."""
    for subfield in subfields:
        data[subfield] = data.apply(lambda row: row[field].get(subfield, '') if row[field] else '', axis=1)
    return data
