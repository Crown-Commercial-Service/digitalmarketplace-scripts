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
