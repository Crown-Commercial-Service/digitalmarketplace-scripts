import json

import backoff
import base64
import requests

from datetime import datetime, timedelta
import dmapiclient

from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging

HOURLY_TIME_FORMAT = '%Y-%m-%dT%H:00:00+00:00'  # On the hour exactly
DAILY_TIME_FORMAT = '%Y-%m-%dT00:00:00+00:00'  # Midnight
PERFORMANCE_PLATFORM_URLS = {
    "day": {
        "stage": "https://www.performance.service.gov.uk/data/gcloud/applications-by-stage",
        "lot": "https://www.performance.service.gov.uk/data/gcloud/applications-by-lot",
    },
    "hour": {
        "stage": "https://www.performance.service.gov.uk/data/gcloud/applications-by-stage-realtime",
        "lot": "https://www.performance.service.gov.uk/data/gcloud/applications-by-lot-realtime",
    },
}

logger = logging_helpers.configure_logger({'dmapiclient': logging.WARNING})


def _format_statistics(stats, category, groupings):
    return _label_and_count(stats[category], groupings)


def _label_and_count(stats, groupings):
    data = {
        label: _sum_counts(stats, filters)
        for label, filters in groupings.items()
    }
    return data


def _sum_counts(stats, filter_by=None, sum_by='count'):
    return sum(
        statistic[sum_by] for statistic in stats
        if not filter_by or all(
            _find(statistic.get(key), value)
            for key, value in filter_by.items()
        )
    )


def _find(statistic, filter_value):
    if isinstance(filter_value, list):
        return statistic in filter_value
    else:
        return statistic == filter_value


def _generate_id(timestamp, period, data_type, data_item):
    # Instructions from Performance Platform:
    # _id should be a unique url-friendly, base64-encoded, UTF8 encoded concatenation identifier, formed from:
    # _timestamp, service (= gcloud), period (= day or hour), dataType (= applications-by-stage/lot), stage/lot
    id_bytes = b'{}-gcloud-{}-{}-{}'.format(timestamp, period, data_type, data_item)
    return base64.b64encode(id_bytes).encode('utf-8')


def send_data(data, url, pp_bearer):
    # Equivalent to
    # curl -X POST -d '<payload>' -H 'Content-type: application/json' -H 'Authorization: Bearer <bearer-token>' <url>
    logger.info(u"Sending data to Performance Platform dataset '{url}':\n{data}", extra={'url': url, 'data': data})
    res = requests.post(url, json=data, headers={'Authorization': 'Bearer {}'.format(pp_bearer)})
    if res.status_code != 200:
        logger.error(
            u"Failed to send data: {code}: {cause}",
            extra={'code': res.status_code, 'cause': res.json().get('message', res.text)}
        )
    return res.status_code


def applications_by_stage(stats):
    return _format_statistics(
        stats,
        'interested_suppliers',
        {
            'interested': {
                'declaration_status': [None, 'started'],
                'has_completed_services': False
            },
            'made-declaration': {
                'declaration_status': 'complete',
                'has_completed_services': False
            },
            'completed-services': {
                'declaration_status': [None, 'started'],
                'has_completed_services': True
            },
            'eligible': {
                'declaration_status': 'complete',
                'has_completed_services': True
            }
        }
    )


def services_by_lot(stats, framework):
    return _format_statistics(
        stats,
        'services',
        {
            lot['slug']: {
                'lot': lot['slug'],
                'status': 'submitted',
            } for lot in framework['lots']
        }
    )


def send_by_stage_stats(stats, timestamp_string, period, pp_bearer):
    data_type = "applications-by-stage"
    processed_stats = applications_by_stage(stats)
    data = [{
        "_id": _generate_id(timestamp_string, period, data_type, stage),
        "_timestamp": timestamp_string,
        "service": "gcloud",
        "stage": stage,
        "count": processed_stats.get(stage, 0),
        "dataType": data_type,
        "period": period
    } for stage in processed_stats]

    return send_data(data, PERFORMANCE_PLATFORM_URLS[period]['stage'], pp_bearer)


def send_by_lot_stats(stats, timestamp_string, period, framework, pp_bearer):
    data_type = "applications-by-lot"
    processed_stats = services_by_lot(stats, framework)
    data = [{
        "_id": _generate_id(timestamp_string, period, data_type, lot),
        "_timestamp": timestamp_string,
        "service": "gcloud",
        "lot": lot,
        "count": processed_stats.get(lot, 0),
        "dataType": data_type,
        "period": period
    } for lot in processed_stats]

    return send_data(data, PERFORMANCE_PLATFORM_URLS[period]['lot'], pp_bearer)


@backoff.on_exception(backoff.expo, dmapiclient.HTTPError, max_tries=5)
def send_framework_stats(data_api_client, framework_slug, period, pp_bearer):
    stats = data_api_client.get_framework_stats(framework_slug)
    framework = data_api_client.get_framework(framework_slug)['frameworks']
    now = datetime.utcnow()
    # _timestamp is the *start* of the period to which the data relates but the "reading" here is at the *end*
    # of the period, so need to subtract the period from the current time
    timestamp_string = (
        (now - timedelta(days=1)).strftime(DAILY_TIME_FORMAT)
        if period == 'day' else
        (now - timedelta(hours=1)).strftime(HOURLY_TIME_FORMAT)
    )
    res1 = send_by_stage_stats(stats, timestamp_string, period, pp_bearer)
    res2 = send_by_lot_stats(stats, timestamp_string, period, framework, pp_bearer)
    return res1 == res2 == 200
