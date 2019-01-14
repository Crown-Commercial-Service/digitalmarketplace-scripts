from io import StringIO

import mock

from dmscripts.export_outcomes_to_csv import export_outcomes_to_csv


@mock.patch('dmapiclient.DataAPIClient', autospec=True)
def test_happy_path(data_api_client):
    data_api_client.find_outcomes_iter.return_value = iter((
        {
            "id": 5678,
            "completed": True,
            "completedAt": "2009-10-11T16:17:18Z",
            "result": "awarded",
            "resultOfDirectAward": {
                "project": {
                    "id": 6789,
                },
                "search": {
                    "id": 7890,
                },
                "archivedService": {
                    "id": 4567,
                    "service": {
                        "id": "23452345",
                    },
                },
            },
            "award": {
                "startDate": "2010-10-10",
                "endDate": "2010-10-11",
                "awardingOrganisationName": "Canteen, Portobello barracks",
                "awardValue": "444345444",
            },
        },
        {
            "id": 5699,
            "completed": True,
            "completedAt": "2009-10-11T19:11:22Z",
            "result": "none-suitable",
            "resultOfDirectAward": {
                "project": {
                    "id": 6789,
                },
            },
        },
        {
            "id": 5677,
            "completed": True,
            "completedAt": "2009-10-12T12:12:12Z",
            "result": "awarded",
            "resultOfDirectAward": {
                "project": {
                    "id": 6777,
                },
                "search": {
                    "id": 7899,
                },
                "archivedService": {
                    "id": 4567,
                    "service": {
                        "id": "23452345",
                    },
                },
            },
            "award": {
                "startDate": "2015-02-02",
                "endDate": "2015-04-20",
                "awardingOrganisationName": "🔑 House of Keyes 🔑",
                "awardValue": "345.67",
            },
            "aKeyToBe": "ignored",
        },
        {
            "id": 5665,
            "completed": True,
            "completedAt": "2009-10-13T12:12:12Z",
            "result": "awarded",
            "resultOfFurtherCompetition": {
                "brief": {
                    "id": 4433,
                },
                "briefResponse": {
                    "id": 6655,
                },
            },
            "award": {
                "startDate": "2009-11-30",
                "endDate": "2009-12-01",
                "awardingOrganisationName": "Boisterous \"Buffalo",
                "awardValue": "888888.6",
            },
        },
        {
            "id": 5699,
            "completed": True,
            "completedAt": "2010-10-10T12:12:12Z",
            "result": "cancelled",
            "resultOfFurtherCompetition": {
                "brief": {
                    "id": 4434,
                },
            },
        },
    ))

    sio_file = StringIO()

    export_outcomes_to_csv(data_api_client, sio_file)

    assert sio_file.getvalue() == (
        "id,completedAt,result,resultOfDirectAward.project.id,resultOfDirectAward.search.id,"
        "resultOfDirectAward.archivedService.service.id,resultOfFurtherCompetition.brief.id,"
        "resultOfFurtherCompetition.briefResponse.id,award.startDate,award.endDate,award.awardingOrganisationName,"
        "award.awardValue\r\n"
        "5678,2009-10-11T16:17:18Z,awarded,6789,7890,23452345,,,2010-10-10,2010-10-11,\"Canteen, Portobello barracks\","
        "444345444\r\n"
        "5699,2009-10-11T19:11:22Z,none-suitable,6789,,,,,,,,\r\n"
        "5677,2009-10-12T12:12:12Z,awarded,6777,7899,23452345,,,2015-02-02,2015-04-20,🔑 House of Keyes 🔑,345.67\r\n"
        "5665,2009-10-13T12:12:12Z,awarded,,,,4433,6655,2009-11-30,2009-12-01,\"Boisterous \"\"Buffalo\",888888.6\r\n"
        "5699,2010-10-10T12:12:12Z,cancelled,,,,4434,,,,,\r\n"
    )
    assert data_api_client.mock_calls == [
        mock.call.find_outcomes_iter(completed=True)
    ]
