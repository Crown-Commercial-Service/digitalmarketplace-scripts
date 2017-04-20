import pytest
import mock
from freezegun import freeze_time
from requests.exceptions import RequestException

from datetime import datetime, date
from lxml import html

from dmscripts.send_dos_opportunities_email import (
    main,
    get_campaign_data,
    create_campaign,
    set_campaign_content,
    send_campaign,
    get_live_briefs_between_two_dates,
    get_html_content
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
    data_api_client.find_briefs_iter.assert_called_once_with(status="live", lot="digital-specialists", human=True)
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

ONE_BRIEF = [
    {
        "title": "Brief 1",
        "organisation": "the big SME",
        "location": "London",
        "applicationsClosedAt": "2016-07-05T23:59:59.000000Z",
        "id": "234",
        "lotName": "Digital specialists"
    },
]
MANY_BRIEFS = [
    {
        "title": "Brief 1",
        "organisation": "the big SME",
        "location": "London",
        "applicationsClosedAt": "2016-07-05T23:59:59.000000Z",
        "id": "234",
        "lotName": "Digital specialists"
    },
    {
        "title": "Brief 2",
        "organisation": "ministry of weird steps",
        "location": "Manchester",
        "applicationsClosedAt": "2016-07-07T23:59:59.000000Z",
        "id": "235",
        "lotName": "Digital specialists"
    }
]


def test_get_html_content_renders_brief_information():
    with freeze_time('2017-04-19 08:00:00'):
        html_content = get_html_content(ONE_BRIEF, 1)["html"]
        doc = html.fromstring(html_content)
        assert doc.xpath('//*[@class="opportunity-title"]')[0].text_content() == ONE_BRIEF[0]["title"]
        assert doc.xpath('//*[@class="opportunity-organisation"]')[0].text_content() == ONE_BRIEF[0]["organisation"]
        assert doc.xpath('//*[@class="opportunity-location"]')[0].text_content() == ONE_BRIEF[0]["location"]
        assert doc.xpath('//*[@class="opportunity-closing"]')[0].text_content() == "Closing Tuesday 5 July 2016"
        assert doc.xpath('//a[@class="opportunity-link"]')[0].text_content() == "https://www.digitalmarketplace.service.gov.uk/digital-outcomes-and-specialists/opportunities/234?utm_id=20170419"  # noqa


def test_get_html_content_renders_multiple_briefs():
    html_content = get_html_content(MANY_BRIEFS, 1)["html"]
    assert "2 new digital specialists opportunities were published" in html_content
    assert "View and apply for these opportunities:" in html_content

    doc = html.fromstring(html_content)
    brief_titles = doc.xpath('//*[@class="opportunity-title"]')
    assert len(brief_titles) == 2
    assert brief_titles[0].text_content() == "Brief 1"
    assert brief_titles[1].text_content() == "Brief 2"


def test_get_html_content_renders_singular_for_single_brief():
    html_content = get_html_content(ONE_BRIEF, 1)["html"]
    assert "1 new digital specialists opportunity was published" in html_content
    assert "View and apply for this opportunity:" in html_content

    doc = html.fromstring(html_content)
    brief_titles = doc.xpath('//*[@class="opportunity-title"]')
    assert len(brief_titles) == 1
    assert brief_titles[0].text_content() == "Brief 1"


def test_get_html_content_with_briefs_from_last_day():
    html_content = get_html_content(ONE_BRIEF, 1)["html"]
    assert "In the last day" in html_content


def test_get_html_content_with_briefs_from_several_days():
    with freeze_time('2017-04-17 08:00:00'):
        html_content = get_html_content(ONE_BRIEF, 3)["html"]
        assert "Since Friday" in html_content


def test_get_campaign_data():
    lot_name = "Digital Outcomes"
    list_id = "1111111"
    expected_subject = "New opportunities for Digital Outcomes: Digital Outcomes and Specialists 2"

    with freeze_time('2017-04-19 08:00:00'):
        campaign_data = get_campaign_data(lot_name, list_id)
        assert campaign_data["recipients"]["list_id"] == list_id
        assert campaign_data["settings"]["subject_line"] == expected_subject
        assert campaign_data["settings"]["title"] == "DOS Suppliers: Digital Outcomes [19 April]"
        assert campaign_data["settings"]["from_name"] == "Digital Marketplace Team"
        assert campaign_data["settings"]["reply_to"] == "do-not-reply@digitalmarketplace.service.gov.uk"


def test_create_campaign():
    mailchimp_client = mock.MagicMock()
    mailchimp_client.campaigns.create.return_value = {"id": "100"}

    res = create_campaign(mailchimp_client, {"example": "data"})
    assert res == "100"
    mailchimp_client.campaigns.create.assert_called_once_with({"example": "data"})


@mock.patch('dmscripts.send_dos_opportunities_email.logger', autospec=True)
def test_log_error_message_if_error_creating_campaign(logger):
    mailchimp_client = mock.MagicMock()
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


def test_set_campaign_content():
    campaign_id = "1"
    html_content = {"html": "<p>One or two words</p>"}
    mailchimp_client = mock.MagicMock()
    mailchimp_client.campaigns.content.update.return_value = html_content

    res = set_campaign_content(mailchimp_client, campaign_id, html_content)
    assert res == html_content
    mailchimp_client.campaigns.content.update.assert_called_once_with(campaign_id, html_content)


@mock.patch('dmscripts.send_dos_opportunities_email.logger', autospec=True)
def test_log_error_message_if_error_setting_campaign_content(logger):
    mailchimp_client = mock.MagicMock()
    mailchimp_client.campaigns.content.update.side_effect = RequestException("error message")
    content_data = {
        "html": "some html"
    }

    assert set_campaign_content(mailchimp_client, "1", content_data) is False
    logger.error.assert_called_once_with(
        "Mailchimp failed to set content for campaign id '1'", extra={"error": "error message"}
    )


def test_send_campaign():
    campaign_id = "1"
    mailchimp_client = mock.MagicMock()
    res = send_campaign(mailchimp_client, campaign_id)
    assert res is True
    mailchimp_client.campaigns.actions.send.assert_called_once_with(campaign_id)


@mock.patch('dmscripts.send_dos_opportunities_email.logger', autospec=True)
def test_log_error_message_if_error_sending_campaign(logger):
    mailchimp_client = mock.MagicMock()
    mailchimp_client.campaigns.actions.send.side_effect = RequestException("error sending")
    assert send_campaign(mailchimp_client, "1") is False
    logger.error.assert_called_once_with(
        "Mailchimp failed to send campaign id '1'", extra={"error": "error sending"}
    )


@mock.patch('dmscripts.send_dos_opportunities_email.get_html_content', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.send_campaign', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.set_campaign_content', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.get_campaign_data', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.create_campaign', autospec=True)
def test_main_creates_campaign_sets_content_and_sends_campaign(
    create_campaign, get_campaign_data, get_live_briefs_between_two_dates,
    set_campaign_content, send_campaign, get_html_content
):
    get_live_briefs_between_two_dates.return_value = [{"brief": "yaytest"}]
    get_campaign_data.return_value = {"created": "campaign"}
    get_html_content.return_value = {"first": "content"}
    create_campaign.return_value = "1"

    main(mock.MagicMock(), mock.MagicMock(), LOT_DATA, 1)

    # Creates campaign
    get_campaign_data.assert_called_once_with("Digital specialists", "096e52cebb")
    create_campaign.assert_called_once_with(mock.ANY, {"created": "campaign"})

    # Sets campaign content
    get_html_content.assert_called_once_with([{"brief": "yaytest"}], 1)
    set_campaign_content.assert_called_once_with(mock.ANY, "1", {"first": "content"})

    # Sends campaign
    send_campaign.assert_called_once_with(mock.ANY, "1")


@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates', autospec=True)
def test_main_gets_live_briefs_for_one_day(get_live_briefs_between_two_dates):
    with freeze_time('2017-04-19 08:00:00'):
        main(mock.MagicMock(), mock.MagicMock(), LOT_DATA, 1)
        get_live_briefs_between_two_dates.assert_called_once_with(
            mock.ANY, "digital-specialists", date(2017, 4, 18), date(2017, 4, 18)
        )


@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates', autospec=True)
def test_main_gets_live_briefs_for_three_days(get_live_briefs_between_two_dates):
    with freeze_time('2017-04-10 08:00:00'):
        main(mock.MagicMock(), mock.MagicMock(), LOT_DATA, 3)
        get_live_briefs_between_two_dates.assert_called_once_with(
            mock.ANY, "digital-specialists", date(2017, 4, 7), date(2017, 4, 9)
        )


@mock.patch('dmscripts.send_dos_opportunities_email.logger', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.send_campaign', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.set_campaign_content', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.create_campaign', autospec=True)
@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates', autospec=True)
def test_if_no_briefs_then_no_campaign_created_nor_sent(
    get_live_briefs_between_two_dates, create_campaign, set_campaign_content, send_campaign, logger
):
    get_live_briefs_between_two_dates.return_value = []
    result = main(mock.MagicMock(), mock.MagicMock(), LOT_DATA, 3)
    assert result is True
    assert create_campaign.call_count == 0
    assert set_campaign_content.call_count == 0
    assert send_campaign.call_count == 0

    logger.info.assert_called_with(
        "No new briefs found for 'digital-specialists' lot", extra={"number_of_days": 3}
    )
