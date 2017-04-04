import pytest
import mock
from freezegun import freeze_time
from requests.exceptions import RequestException

import datetime

from dmscripts.send_dos_opportunities_email import (
    main,
    create_campaign_data,
    create_campaign,
    set_campaign_content,
    send_campaign
)


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


@mock.patch('dmscripts.send_dos_opportunities_email.get_mailchimp_client')
@mock.patch('dmscripts.send_dos_opportunities_email.create_campaign_data')
@mock.patch('dmscripts.send_dos_opportunities_email.create_campaign')
def test_main_creates_campaigns_for_each_lot(create_campaign, create_campaign_data, get_mailchimp_client):
    create_campaign_data.side_effect = [{"first": "campaign"}, {"second": "campaign"}, {"third": "campaign"}]

    main("username", "API KEY")

    create_campaign_data.assert_any_call("Digital specialists", "096e52cebb")
    create_campaign.assert_any_call(mock.ANY, {"first": "campaign"})

    create_campaign_data.assert_any_call("Digital outcomes", "096e52cebb")
    create_campaign.assert_any_call(mock.ANY, {"second": "campaign"})

    create_campaign_data.assert_any_call("User research participants", "096e52cebb")
    create_campaign.assert_any_call(mock.ANY, {"third": "campaign"})


@mock.patch('dmscripts.send_dos_opportunities_email.create_campaign')
@mock.patch('dmscripts.send_dos_opportunities_email.get_html_content')
@mock.patch('dmscripts.send_dos_opportunities_email.get_mailchimp_client')
@mock.patch('dmscripts.send_dos_opportunities_email.set_campaign_content')
def test_main_sets_content_for_each_lot(set_campaign_content, get_mailchimp_client, get_html_content, create_campaign):
    get_html_content.side_effect = [{"first": "content"}, {"second": "content"}, {"third": "content"}]
    create_campaign.side_effect = ["1", "2", "3"]
    main("username", "API KEY")

    get_html_content.assert_any_call()
    set_campaign_content.assert_any_call(mock.ANY, "1", {"first": "content"})

    get_html_content.assert_any_call()
    set_campaign_content.assert_any_call(mock.ANY, "2", {"second": "content"})

    get_html_content.assert_any_call()
    set_campaign_content.assert_any_call(mock.ANY, "3", {"third": "content"})


@mock.patch('dmscripts.send_dos_opportunities_email.create_campaign')
@mock.patch('dmscripts.send_dos_opportunities_email.get_mailchimp_client')
@mock.patch('dmscripts.send_dos_opportunities_email.send_campaign')
def test_main_sends_campaign_for_each_lot(send_campaign, get_mailchimp_client, create_campaign):
    create_campaign.side_effect = ["1", "2", "3"]
    main("username", "API KEY")
    send_campaign.assert_any_call(mock.ANY, "1")
    send_campaign.assert_any_call(mock.ANY, "2")
    send_campaign.assert_any_call(mock.ANY, "3")
