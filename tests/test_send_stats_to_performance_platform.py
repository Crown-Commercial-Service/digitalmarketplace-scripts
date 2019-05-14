import json

import mock

from dmscripts.send_stats_to_performance_platform import applications_by_stage, services_by_lot, send_by_stage_stats, \
    send_by_lot_stats

FRAMEWORK_JSON = json.loads('''
{
    "frameworks": {
        "lots": [
            {"slug": "cloud-hosting"},
            {"slug": "cloud-software"},
            {"slug": "cloud-support"}
        ]
    }
}
''')

STATS_JSON = json.loads('''
{
   "services": [
      {
         "count": 13,
         "status": "not-submitted",
         "declaration_made": false,
         "lot": "cloud-hosting"
      },
      {
         "count": 17,
         "status": "not-submitted",
         "declaration_made": true,
         "lot": "cloud-hosting"
      },
      {
         "count": 19,
         "status": "not-submitted",
         "declaration_made": false,
         "lot": "cloud-software"
      },
      {
         "count": 23,
         "status": "not-submitted",
         "declaration_made": true,
         "lot": "cloud-software"
      },
      {
         "count": 29,
         "status": "not-submitted",
         "declaration_made": false,
         "lot": "cloud-support"
      },
      {
         "count": 31,
         "status": "not-submitted",
         "declaration_made": true,
         "lot": "cloud-support"
      },
      {
         "count": 37,
         "status": "submitted",
         "declaration_made": true,
         "lot": "cloud-hosting"
      },
      {
         "count": 41,
         "status": "submitted",
         "declaration_made": true,
         "lot": "cloud-software"
      },
      {
         "count": 43,
         "status": "submitted",
         "declaration_made": true,
         "lot": "cloud-support"
      },
            {
         "count": 47,
         "status": "submitted",
         "declaration_made": false,
         "lot": "cloud-hosting"
      },
      {
         "count": 53,
         "status": "submitted",
         "declaration_made": false,
         "lot": "cloud-software"
      },
      {
         "count": 59,
         "status": "submitted",
         "declaration_made": false,
         "lot": "cloud-support"
      }
   ],
   "interested_suppliers": [
      {
         "count": 101,
         "declaration_status": null,
         "has_completed_services": false
      },
      {
         "count": 97,
         "declaration_status": "complete",
         "has_completed_services": false
      },
      {
         "count": 89,
         "declaration_status": "complete",
         "has_completed_services": true
      },
      {
         "count": 83,
         "declaration_status": "started",
         "has_completed_services": false
      },
      {
         "count": 79,
         "declaration_status": "started",
         "has_completed_services": true
      }
   ],
   "supplier_users": [
      {
         "count": 7654,
         "recent_login": false
      },
      {
         "count": 4567,
         "recent_login": null
      },
      {
         "count": 2345,
         "recent_login": true
      }
   ]
}
''')


def test_applications_by_stage():
    assert applications_by_stage(STATS_JSON) == {
        'completed-services': 79,  # 79 - incomplete declaration plus completed services
        'eligible': 89,            # 89 - complete declaration plus completed services
        'interested': 184,         # 101 + 83 - incomplete declaration and no services
        'made-declaration': 97     # 97 - complete declaration and no services
    }


def test_services_by_lot():
    assert services_by_lot(STATS_JSON, FRAMEWORK_JSON['frameworks']) == {
        'cloud-hosting': 84,   # 37 + 47 submitted with or without complete declaration
        'cloud-software': 94,  # 41 + 53 submitted with or without complete declaration
        'cloud-support': 102    # 43 + 59 submitted with or without complete declaration
    }


@mock.patch('dmscripts.send_stats_to_performance_platform.send_data')
def test_send_by_stage_stats_per_day_calls_send_data_with_correct_data(send_data):
    send_by_stage_stats(STATS_JSON, '2017-03-29T00:00:00+00:00', 'day', 'pp-bearer-token', 'gcloud', dry_run=False)
    expected_sent_data_items = [
        {'count': 184,
         '_timestamp': '2017-03-29T00:00:00+00:00',
         'service': 'gcloud',
         'dataType': 'applications-by-stage',
         'period': 'day',
         # Base 64 encoding of '2017-03-29T00:00:00+00:00-gcloud-day-applications-by-stage-interested'
         '_id': 'MjAxNy0wMy0yOVQwMDowMDowMCswMDowMC1nY2xvdWQtZGF5LWFwcGxpY2F0aW9ucy1ieS1zdGFnZS1pbnRlcmVzdGVk',
         'stage': 'interested'
        },
        {'count': 97,
         '_timestamp': '2017-03-29T00:00:00+00:00',
         'service': 'gcloud',
         'dataType': 'applications-by-stage',
         'period': 'day',
         # Base 64 encoding of '2017-03-29T00:00:00+00:00-gcloud-day-applications-by-stage-made-declaration'
         '_id': 'MjAxNy0wMy0yOVQwMDowMDowMCswMDowMC1nY2xvdWQtZGF5LWFwcGxpY2F0aW9ucy1ieS1zdGFnZS1tYWRlLWRlY2xhcmF0aW9u',  # noqa
         'stage': 'made-declaration'
         },
        {'count': 79,
         '_timestamp': '2017-03-29T00:00:00+00:00',
         'service': 'gcloud',
         'dataType': 'applications-by-stage',
         'period': 'day',
         # Base 64 encoding of '2017-03-29T00:00:00+00:00-gcloud-day-applications-by-stage-completed-services'
         '_id': 'MjAxNy0wMy0yOVQwMDowMDowMCswMDowMC1nY2xvdWQtZGF5LWFwcGxpY2F0aW9ucy1ieS1zdGFnZS1jb21wbGV0ZWQtc2VydmljZXM=',  # noqa
         'stage': 'completed-services'
         },
        {'count': 89,
         '_timestamp': '2017-03-29T00:00:00+00:00',
         'service': 'gcloud',
         'dataType': 'applications-by-stage',
         'period': 'day',
         # Base 64 encoding of '2017-03-29T00:00:00+00:00-gcloud-day-applications-by-stage-eligible'
         '_id': 'MjAxNy0wMy0yOVQwMDowMDowMCswMDowMC1nY2xvdWQtZGF5LWFwcGxpY2F0aW9ucy1ieS1zdGFnZS1lbGlnaWJsZQ==',
         'stage': 'eligible'
         }
    ]
    # Python 2 and Python 3 can generate the data in varying order, so test items independent of order in the list
    sent_data = send_data.call_args[0][0]
    assert len(sent_data) == 4
    for item in sent_data:
        assert item in expected_sent_data_items
        expected_sent_data_items.remove(item)  # Each item should appear once in the call args so remove once found

    send_data.assert_called_with(
        mock.ANY,  # Data sent has already been tested above
        'https://www.performance.service.gov.uk/data/gcloud/applications-by-stage',
        'pp-bearer-token'
    )


@mock.patch('dmscripts.send_stats_to_performance_platform.send_data')
def test_send_by_stage_stats_per_hour_calls_send_data_with_correct_data(send_data):
    send_by_stage_stats(STATS_JSON, '2017-03-29T12:00:00+00:00', 'hour', 'pp-bearer-token', 'hcloud', dry_run=False)
    expected_sent_data_items = [
        {'count': 184,
         '_timestamp': '2017-03-29T12:00:00+00:00',
         'service': 'hcloud',
         'dataType': 'applications-by-stage',
         'period': 'hour',
         # Base 64 encoding of '2017-03-29T12:00:00+00:00-hcloud-hour-applications-by-stage-interested'
         '_id': 'MjAxNy0wMy0yOVQxMjowMDowMCswMDowMC1oY2xvdWQtaG91ci1hcHBsaWNhdGlvbnMtYnktc3RhZ2UtaW50ZXJlc3RlZA==',
         'stage': 'interested'
         },
        {'count': 97,
         '_timestamp': '2017-03-29T12:00:00+00:00',
         'service': 'hcloud',
         'dataType': 'applications-by-stage',
         'period': 'hour',
         # Base 64 encoding of '2017-03-29T12:00:00+00:00-hcloud-hour-applications-by-stage-made-declaration'
         '_id': 'MjAxNy0wMy0yOVQxMjowMDowMCswMDowMC1oY2xvdWQtaG91ci1hcHBsaWNhdGlvbnMtYnktc3RhZ2UtbWFkZS1kZWNsYXJhdGlvbg==',  # noqa
         'stage': 'made-declaration'
         },
        {'count': 79,
         '_timestamp': '2017-03-29T12:00:00+00:00',
         'service': 'hcloud',
         'dataType': 'applications-by-stage',
         'period': 'hour',
         # Base 64 encoding of '2017-03-29T12:00:00+00:00-hcloud-hour-applications-by-stage-completed-services'
         '_id': 'MjAxNy0wMy0yOVQxMjowMDowMCswMDowMC1oY2xvdWQtaG91ci1hcHBsaWNhdGlvbnMtYnktc3RhZ2UtY29tcGxldGVkLXNlcnZpY2Vz',  # noqa
         'stage': 'completed-services'
         },
        {'count': 89,
         '_timestamp': '2017-03-29T12:00:00+00:00',
         'service': 'hcloud',
         'dataType': 'applications-by-stage',
         'period': 'hour',
         # Base 64 encoding of '2017-03-29T12:00:00+00:00-hcloud-hour-applications-by-stage-eligible'
         '_id': 'MjAxNy0wMy0yOVQxMjowMDowMCswMDowMC1oY2xvdWQtaG91ci1hcHBsaWNhdGlvbnMtYnktc3RhZ2UtZWxpZ2libGU=',
         'stage': 'eligible'
         },
    ]
    # Python 2 and Python 3 can generate the data in varying order, so test items independent of order in the list
    sent_data = send_data.call_args[0][0]
    assert len(sent_data) == 4
    for item in sent_data:
        assert item in expected_sent_data_items
        expected_sent_data_items.remove(item)  # Each item should appear once in the call args so remove once found

    send_data.assert_called_with(
        mock.ANY,  # Data sent has already been tested above
        'https://www.performance.service.gov.uk/data/hcloud/applications-by-stage-realtime',
        'pp-bearer-token'
    )


@mock.patch('dmscripts.send_stats_to_performance_platform.send_data')
def test_send_by_lot_stats_per_day_calls_send_data_with_correct_data(send_data):
    send_by_lot_stats(
        STATS_JSON,
        '2017-03-29T00:00:00+00:00',
        'day',
        FRAMEWORK_JSON['frameworks'],
        'pp-bearer-token',
        'gcloud',
        dry_run=False
    )
    expected_sent_data_items = [
        {'count': 84,
         '_timestamp': '2017-03-29T00:00:00+00:00',
         'service': 'gcloud',
         'dataType': 'applications-by-lot',
         'period': 'day',
         'lot': 'cloud-hosting',
         # Base 64 encoding of '2017-03-29T00:00:00+00:00-gcloud-day-applications-by-lot-cloud-hosting'
         '_id': 'MjAxNy0wMy0yOVQwMDowMDowMCswMDowMC1nY2xvdWQtZGF5LWFwcGxpY2F0aW9ucy1ieS1sb3QtY2xvdWQtaG9zdGluZw=='
         },
        {'count': 102,
         '_timestamp': '2017-03-29T00:00:00+00:00',
         'service': 'gcloud',
         'dataType': 'applications-by-lot',
         'period': 'day',
         'lot': 'cloud-support',
         # Base 64 encoding of '2017-03-29T00:00:00+00:00-gcloud-day-applications-by-lot-cloud-support'
         '_id': 'MjAxNy0wMy0yOVQwMDowMDowMCswMDowMC1nY2xvdWQtZGF5LWFwcGxpY2F0aW9ucy1ieS1sb3QtY2xvdWQtc3VwcG9ydA=='
         },
        {'count': 94,
         '_timestamp': '2017-03-29T00:00:00+00:00',
         'service': 'gcloud',
         'dataType': 'applications-by-lot',
         'period': 'day',
         'lot': 'cloud-software',
         # Base 64 encoding of '2017-03-29T00:00:00+00:00-gcloud-day-applications-by-lot-cloud-software'
         '_id': 'MjAxNy0wMy0yOVQwMDowMDowMCswMDowMC1nY2xvdWQtZGF5LWFwcGxpY2F0aW9ucy1ieS1sb3QtY2xvdWQtc29mdHdhcmU='
         }
    ]

    # Python 2 and Python 3 can generate the data in varying order, so test items independent of order in the list
    sent_data = send_data.call_args[0][0]
    assert len(sent_data) == 3
    for item in sent_data:
        assert item in expected_sent_data_items
        expected_sent_data_items.remove(item)  # Each item should appear once in the call args so remove once found

    send_data.assert_called_with(
        mock.ANY,  # Data sent has already been tested above
        'https://www.performance.service.gov.uk/data/gcloud/applications-by-lot',
        'pp-bearer-token'
    )


@mock.patch('dmscripts.send_stats_to_performance_platform.send_data')
def test_send_by_lot_stats_per_hour_calls_send_data_with_correct_data(send_data):
    send_by_lot_stats(
        STATS_JSON,
        '2017-03-29T12:00:00+00:00',
        'hour',
        FRAMEWORK_JSON['frameworks'],
        'pp-bearer-token',
        'gcloud',
        dry_run=False
    )
    expected_sent_data_items = [
        {'count': 84,
         '_timestamp': '2017-03-29T12:00:00+00:00',
         'service': 'gcloud',
         'dataType': 'applications-by-lot',
         'period': 'hour',
         'lot': 'cloud-hosting',
         # Base 64 encoding of '2017-03-29T12:00:00+00:00-gcloud-hour-applications-by-lot-cloud-hosting'
         '_id': 'MjAxNy0wMy0yOVQxMjowMDowMCswMDowMC1nY2xvdWQtaG91ci1hcHBsaWNhdGlvbnMtYnktbG90LWNsb3VkLWhvc3Rpbmc='
         },
        {'count': 102,
         '_timestamp': '2017-03-29T12:00:00+00:00',
         'service': 'gcloud',
         'dataType': 'applications-by-lot',
         'period': 'hour',
         'lot': 'cloud-support',
         # Base 64 encoding of '2017-03-29T12:00:00+00:00-gcloud-hour-applications-by-lot-cloud-support'
         '_id': 'MjAxNy0wMy0yOVQxMjowMDowMCswMDowMC1nY2xvdWQtaG91ci1hcHBsaWNhdGlvbnMtYnktbG90LWNsb3VkLXN1cHBvcnQ='
         },
        {'count': 94,
         '_timestamp': '2017-03-29T12:00:00+00:00',
         'service': 'gcloud',
         'dataType': 'applications-by-lot',
         'period': 'hour',
         'lot': 'cloud-software',
         # Base 64 encoding of '2017-03-29T12:00:00+00:00-gcloud-hour-applications-by-lot-cloud-software'
         '_id': 'MjAxNy0wMy0yOVQxMjowMDowMCswMDowMC1nY2xvdWQtaG91ci1hcHBsaWNhdGlvbnMtYnktbG90LWNsb3VkLXNvZnR3YXJl'
         }
    ]

    # Python 2 and Python 3 can generate the data in varying order, so test items independent of order in the list
    sent_data = send_data.call_args[0][0]
    assert len(sent_data) == 3
    for item in sent_data:
        assert item in expected_sent_data_items
        expected_sent_data_items.remove(item)  # Each item should appear once in the call args so remove once found

    send_data.assert_called_with(
        mock.ANY,  # Data sent has already been tested above
        'https://www.performance.service.gov.uk/data/gcloud/applications-by-lot-realtime',
        'pp-bearer-token'
    )
