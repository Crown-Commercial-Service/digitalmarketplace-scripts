import pytest
import mock
from freezegun import freeze_time
from requests.exceptions import RequestException

from datetime import datetime, date

from dmscripts.send_dos_opportunities_email import (
    main,
    create_campaign_data,
    create_campaign,
    set_campaign_content,
    send_campaign,
    get_live_briefs_between_two_dates
)

LOT_DATA = {
    "lot_slug": "digital-specialists",
    "lot_name": "Digital specialists",
    "list_id": "096e52cebb"
}


def test_get_live_briefs_between_two_dates():
    data_api_client = mock.Mock()
    brief_iter_values = [
        {"publishedAt": "2017-03-24T09:52:17.669156Z"},
        {"publishedAt": "2017-03-23T23:59:59.669156Z"},
        {"publishedAt": "2017-03-23T09:52:17.669156Z"},
        {"publishedAt": "2017-03-23T00:00:00.000000Z"},
        {"publishedAt": "2017-03-22T09:52:17.669156Z"},
        {"publishedAt": "2017-03-21T09:52:17.669156Z"},
        {"publishedAt": "2017-03-20T09:52:17.669156Z"},
        {"publishedAt": "2017-03-19T09:52:17.669156Z"},
        {"publishedAt": "2017-03-18T09:52:17.669156Z"},
        {"publishedAt": "2017-02-17T09:52:17.669156Z"}
    ]

    data_api_client.find_briefs_iter.return_value = iter(brief_iter_values)
    briefs = get_live_briefs_between_two_dates(
        data_api_client, "digital-specialists", date(2017, 3, 23), date(2017, 3, 23)
    )
    data_api_client.find_briefs_iter.assert_called_once_with(status="live", lot="digital-specialists")
    assert briefs == [
        {"publishedAt": "2017-03-23T23:59:59.669156Z"},
        {"publishedAt": "2017-03-23T09:52:17.669156Z"},
        {"publishedAt": "2017-03-23T00:00:00.000000Z"}
    ]

    data_api_client.find_briefs_iter.return_value = iter(brief_iter_values)
    briefs = get_live_briefs_between_two_dates(
        data_api_client, "digital-specialists", date(2017, 3, 18), date(2017, 3, 20)
    )
    assert briefs == [
        {"publishedAt": "2017-03-20T09:52:17.669156Z"},
        {"publishedAt": "2017-03-19T09:52:17.669156Z"},
        {"publishedAt": "2017-03-18T09:52:17.669156Z"}
    ]


def test_create_campaign_data():
    lot_name = "Digital Outcomes"
    list_id = "1111111"
    expected_subject = "New opportunities for Digital Outcomes: Digital Outcomes and Specialists 2"

    with freeze_time('2017-04-19 08:00:00'):
        campaign_data = create_campaign_data(lot_name, list_id)
        assert campaign_data["recipients"]["list_id"] == list_id
        assert campaign_data["settings"]["subject_line"] == expected_subject
        assert campaign_data["settings"]["title"] == "DOS Suppliers: Digital Outcomes [19 April]"
        assert campaign_data["settings"]["from_name"] == "Digital Marketplace Team"
        assert campaign_data["settings"]["reply_to"] == "do-not-reply@digitalmarketplace.service.gov.uk"


@mock.patch('dmscripts.send_dos_opportunities_email.MailChimp')
def test_create_campaign(mailchimp_client):
    mailchimp_client.campaigns.create.return_value = {"id": "100"}

    res = create_campaign(mailchimp_client, {"example": "data"})
    assert res == "100"
    mailchimp_client.campaigns.create.assert_called_once_with({"example": "data"})


@mock.patch('dmscripts.send_dos_opportunities_email.logger', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.MailChimp')
def test_log_error_message_if_error_creating_campaign(mailchimp_client, logger):
    mailchimp_client.campaigns.create.side_effect = RequestException("error message")
    campaign_data = {
        "example": "data",
        "settings": {
            "title": "campaign title"
        }
    }

    assert create_campaign(mailchimp_client, campaign_data) is False
    logger.error.assert_called_once_with(
        "Mailchimp failed to create campaign for 'campaign title'", extra={"error": "error message"}
    )


@mock.patch('dmscripts.send_dos_opportunities_email.MailChimp')
def test_set_campaign_content(mailchimp_client):
    campaign_id = "1"
    html_content = {"html": "<p>One or two words</p>"}
    mailchimp_client.campaigns.content.update.return_value = html_content

    res = set_campaign_content(mailchimp_client, campaign_id, html_content)
    assert res == html_content
    mailchimp_client.campaigns.content.update.assert_called_once_with(campaign_id, html_content)


@mock.patch('dmscripts.send_dos_opportunities_email.logger', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.MailChimp')
def test_log_error_message_if_error_setting_campaign_content(mailchimp_client, logger):
    mailchimp_client.campaigns.content.update.side_effect = RequestException("error message")
    content_data = {
        "html": "some html"
    }

    assert set_campaign_content(mailchimp_client, "1", content_data) is False
    logger.error.assert_called_once_with(
        "Mailchimp failed to set content for campaign id '1'", extra={"error": "error message"}
    )


@mock.patch('dmscripts.send_dos_opportunities_email.MailChimp')
def test_send_campaign(mailchimp_client):
    campaign_id = "1"
    res = send_campaign(mailchimp_client, campaign_id)
    assert res is True
    mailchimp_client.campaigns.actions.send.assert_called_once_with(campaign_id)


@mock.patch('dmscripts.send_dos_opportunities_email.logger', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.MailChimp')
def test_log_error_message_if_error_sending_campaign(mailchimp_client, logger):
    mailchimp_client.campaigns.actions.send.side_effect = RequestException("error sending")
    assert send_campaign(mailchimp_client, "1") is False
    logger.error.assert_called_once_with(
        "Mailchimp failed to send campaign id '1'", extra={"error": "error sending"}
    )


@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates')
@mock.patch('dmscripts.send_dos_opportunities_email.get_mailchimp_client')
@mock.patch('dmscripts.send_dos_opportunities_email.create_campaign_data')
@mock.patch('dmscripts.send_dos_opportunities_email.create_campaign')
def test_main_creates_campaigns(
    create_campaign, create_campaign_data, get_mailchimp_client, get_live_briefs_between_two_dates
):
    create_campaign_data.return_value = {"created": "campaign"}

    main("data_api_url", "data_api_access_token", "username", "API KEY", LOT_DATA, 1)
    create_campaign_data.assert_called_once_with("Digital specialists", "096e52cebb")
    create_campaign.assert_called_once_with(mock.ANY, {"created": "campaign"})


@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates')
@mock.patch('dmscripts.send_dos_opportunities_email.create_campaign')
@mock.patch('dmscripts.send_dos_opportunities_email.get_html_content')
@mock.patch('dmscripts.send_dos_opportunities_email.get_mailchimp_client')
@mock.patch('dmscripts.send_dos_opportunities_email.set_campaign_content')
def test_main_sets_content(
    set_campaign_content, get_mailchimp_client, get_html_content, create_campaign, get_live_briefs_between_two_dates
):
    get_html_content.return_value = {"first": "content"}
    create_campaign.return_value = "1"

    main("data_api_url", "data_api_access_token", "username", "API KEY", LOT_DATA, 1)
    get_html_content.assert_called_once_with()
    set_campaign_content.assert_called_once_with(mock.ANY, "1", {"first": "content"})


@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates')
@mock.patch('dmscripts.send_dos_opportunities_email.create_campaign')
@mock.patch('dmscripts.send_dos_opportunities_email.get_mailchimp_client')
@mock.patch('dmscripts.send_dos_opportunities_email.send_campaign')
def test_main_sends_campaign(
    send_campaign, get_mailchimp_client, create_campaign, get_live_briefs_between_two_dates
):
    create_campaign.return_value = "1"

    main("data_api_url", "data_api_access_token", "username", "API KEY", LOT_DATA, 1)
    send_campaign.assert_called_once_with(mock.ANY, "1")


@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates')
def test_main_gets_live_briefs_for_one_day(get_live_briefs_between_two_dates):
    with freeze_time('2017-04-19 08:00:00'):
        main("data_api_url", "data_api_access_token", "username", "API KEY", LOT_DATA, 1)
        get_live_briefs_between_two_dates.assert_called_once_with(
            mock.ANY, "digital-specialists", date(2017, 4, 18), date(2017, 4, 18)
        )


@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates')
def test_main_gets_live_briefs_for_three_days(get_live_briefs_between_two_dates):
    with freeze_time('2017-04-10 08:00:00'):
        main("data_api_url", "data_api_access_token", "username", "API KEY", LOT_DATA, 3)
        get_live_briefs_between_two_dates.assert_called_once_with(
            mock.ANY, "digital-specialists", date(2017, 4, 7), date(2017, 4, 9)
        )


@mock.patch('dmscripts.send_dos_opportunities_email.logger', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.send_campaign')
@mock.patch('dmscripts.send_dos_opportunities_email.set_campaign_content')
@mock.patch('dmscripts.send_dos_opportunities_email.create_campaign')
@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates')
def test_if_no_briefs_then_no_campaign_created_nor_sent(
    get_live_briefs_between_two_dates, create_campaign, set_campaign_content, send_campaign, logger
):
    get_live_briefs_between_two_dates.return_value = []
    result = main("data_api_url", "data_api_access_token", "username", "API KEY", LOT_DATA, 3)
    assert result is True
    create_campaign.assert_not_called()
    set_campaign_content.assert_not_called()
    send_campaign.assert_not_called()

    logger.info.assert_called_once_with(
        "No new briefs found for 'digital-specialists' lot", extra={"number_of_days": 3}
    )
