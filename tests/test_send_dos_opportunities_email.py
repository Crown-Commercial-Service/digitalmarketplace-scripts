import mock
from datetime import date

from freezegun import freeze_time
from lxml import html

from dmscripts.send_dos_opportunities_email import (
    main,
    get_campaign_data,
    get_live_briefs_between_two_dates,
    get_live_briefs_by_framework_and_lot,
    get_html_content
)
from dmutils.email.dm_mailchimp import DMMailChimpClient
from dmapiclient import DataAPIClient


class TestGetLiveBriefsBetweenTwoDates:

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

    def test_get_live_briefs_between_two_dates_single_day(self):
        data_api_client = mock.Mock()

        data_api_client.find_briefs_iter.return_value = iter(self.brief_iter_values)

        briefs = get_live_briefs_between_two_dates(data_api_client, date(2017, 3, 23), date(2017, 3, 23),)

        assert data_api_client.find_briefs_iter.call_args_list == [
            mock.call(status="live", human=True)
        ]
        assert briefs == [
            {"publishedAt": "2017-03-23T23:59:59.669156Z"},
            {"publishedAt": "2017-03-23T09:52:17.669156Z"},
            {"publishedAt": "2017-03-23T00:00:00.000000Z"}
        ]

    def test_get_live_briefs_between_two_dates_multi_day(self):
        data_api_client = mock.Mock()
        data_api_client.find_briefs_iter.return_value = iter(self.brief_iter_values)
        briefs = get_live_briefs_between_two_dates(
            data_api_client, date(2017, 3, 18), date(2017, 3, 20),

        )
        assert briefs == [
            {"publishedAt": "2017-03-20T09:52:17.669156Z"},
            {"publishedAt": "2017-03-19T09:52:17.669156Z"},
            {"publishedAt": "2017-03-18T09:52:17.669156Z"}
        ]


BRIEF_1 = {
    "title": "Brief 1",
    "organisation": "the big SME",
    "location": "London",
    "applicationsClosedAt": "2016-07-05T23:59:59.000000Z",
    "id": "234",
    "lotName": "Digital specialists",
    "lotSlug": "digital-specialists",
    "frameworkSlug": "digital-outcomes-and-specialists-3",
    "frameworkName": "Digital Outcomes and Specialists 3"
}


BRIEF_2 = {
    "title": "Brief 2",
    "organisation": "ministry of weird steps",
    "location": "Manchester",
    "applicationsClosedAt": "2016-07-07T23:59:59.000000Z",
    "id": "235",
    "lotName": "Digital specialists",
    "lotSlug": "digital-specialists",
    "frameworkSlug": "digital-outcomes-and-specialists-3",
    "frameworkName": "Digital Outcomes and Specialists 3"
}

BRIEF_3 = {
    "title": "Brief 3",
    "organisation": "ministry of OK steps",
    "location": "Glasgow",
    "applicationsClosedAt": "2016-07-08T23:59:59.000000Z",
    "id": "236",
    "lotName": "Digital outcomes",
    "lotSlug": "digital-outcomes",
    "frameworkSlug": "digital-outcomes-and-specialists-4",
    "frameworkName": "Digital Outcomes and Specialists 4"
}

BRIEF_4 = {
    "title": "Brief 4",
    "organisation": "ministry of amazing steps",
    "location": "Truro",
    "applicationsClosedAt": "2016-07-08T23:59:59.000000Z",
    "id": "237",
    "lotName": "User research participants",
    "lotSlug": "user-research-participants",
    "frameworkSlug": "digital-outcomes-and-specialists-4",
    "frameworkName": "Digital Outcomes and Specialists 4"
}


class TestGetHTMLContent:

    def test_get_html_content_renders_brief_information(self):
        with freeze_time('2017-04-19 08:00:00'):
            html_content = get_html_content([BRIEF_1], 1)["html"]
            doc = html.fromstring(html_content)

            assert doc.xpath('//*[@class="opportunity-title"]')[0].text_content() == BRIEF_1["title"]
            assert doc.xpath('//*[@class="opportunity-organisation"]')[0].text_content() == BRIEF_1["organisation"]
            assert doc.xpath('//*[@class="opportunity-location"]')[0].text_content() == BRIEF_1["location"]
            assert doc.xpath('//*[@class="opportunity-closing"]')[0].text_content() == "Closing Tuesday 5 July 2016"
            assert doc.xpath('//a[@class="opportunity-link"]')[0].text_content() == "https://www.digitalmarketplace.service.gov.uk/digital-outcomes-and-specialists/opportunities/234?utm_id=20170419"  # noqa

    def test_get_html_content_renders_multiple_briefs(self):
        html_content = get_html_content([BRIEF_1, BRIEF_2], 1)["html"]
        doc = html.fromstring(html_content)
        brief_titles = doc.xpath('//*[@class="opportunity-title"]')

        assert "2 new digital specialists opportunities were published" in html_content
        assert "View and apply for these opportunities:" in html_content

        assert len(brief_titles) == 2
        assert brief_titles[0].text_content() == "Brief 1"
        assert brief_titles[1].text_content() == "Brief 2"

    def test_get_html_content_renders_singular_for_single_brief(self):
        html_content = get_html_content([BRIEF_1], 1)["html"]
        doc = html.fromstring(html_content)
        brief_titles = doc.xpath('//*[@class="opportunity-title"]')

        assert "1 new digital specialists opportunity was published" in html_content
        assert "View and apply for this opportunity:" in html_content

        assert len(brief_titles) == 1
        assert brief_titles[0].text_content() == "Brief 1"

    def test_get_html_content_with_briefs_from_last_day(self):
        html_content = get_html_content([BRIEF_1], 1)["html"]
        assert "In the last day" in html_content

    def test_get_html_content_with_briefs_from_several_days(self):
        with freeze_time('2017-04-17 08:00:00'):
            html_content = get_html_content([BRIEF_1], 3)["html"]
            assert "Since Friday" in html_content


class TestGetCampaignData:

    def test_get_campaign_data(self):
        framework_name = "Digit Outcomes and Specialists Two"
        lot_name = "Digital Somethings"
        list_id = "1111111"

        with freeze_time('2017-04-19 08:00:00'):
            campaign_data = get_campaign_data(lot_name, list_id, framework_name)
            assert campaign_data["recipients"]["list_id"] == list_id
            assert campaign_data["settings"]["subject_line"] == f"New opportunities for {lot_name}: {framework_name}"
            assert campaign_data["settings"]["title"] == f"DOS Suppliers: {lot_name} [19 April]"
            assert campaign_data["settings"]["from_name"] == "Digital Marketplace Team"
            assert campaign_data["settings"]["reply_to"] == "do-not-reply@digitalmarketplace.service.gov.uk"


class TestGetLiveBriefsByFrameworkAndLot:

    @mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_between_two_dates', autospec=True)
    def test_get_live_briefs_by_framework_and_lot_groups_briefs_by_framework(self, get_live_briefs_between_two_dates):
        client = mock.Mock(spec=DataAPIClient)
        get_live_briefs_between_two_dates.return_value = [BRIEF_1, BRIEF_2, BRIEF_3, BRIEF_4]

        result = get_live_briefs_by_framework_and_lot(client, date(2017, 4, 18), date(2017, 4, 18))
        assert result == {
            'digital-outcomes-and-specialists-3': {
                'digital-specialists': [BRIEF_1, BRIEF_2]
            },
            'digital-outcomes-and-specialists-4': {
                'digital-outcomes': [BRIEF_3],
                'user-research-participants': [BRIEF_4],
            }
        }
        assert get_live_briefs_between_two_dates.call_args_list == [
            mock.call(client, date(2017, 4, 18), date(2017, 4, 18))
        ]


@mock.patch('dmscripts.send_dos_opportunities_email.get_live_briefs_by_framework_and_lot', autospec=True)
class TestSendDOSOpportunitiesEmail:

    def setup_method(self):
        self.data_api_client = mock.Mock(spec=DataAPIClient)
        self.dm_mailchimp_client = mock.Mock(spec=DMMailChimpClient)

    @mock.patch('dmscripts.send_dos_opportunities_email.get_html_content', autospec=True)
    @mock.patch('dmscripts.send_dos_opportunities_email.get_campaign_data', autospec=True)
    def test_main_creates_campaign_sets_content_and_sends_campaign_for_all_frameworks_and_lots(
        self, get_campaign_data, get_html_content, get_live_briefs_by_framework_and_lot
    ):
        get_live_briefs_by_framework_and_lot.return_value = {
            'digital-outcomes-and-specialists-3': {
                'digital-specialists': [BRIEF_1, BRIEF_2]
            },
            'digital-outcomes-and-specialists-4': {
                'digital-outcomes': [BRIEF_3],
                'user-research-participants': [BRIEF_4],
            }
        }
        get_campaign_data.return_value = {"created": "campaign"}
        get_html_content.return_value = {"first": "content"}
        self.dm_mailchimp_client.create_campaign.return_value = "1"

        assert main(
            self.data_api_client,
            self.dm_mailchimp_client,
            1,
            framework_override=None,
            list_id_override="096e52cebb",
            lot_slug_override=None
        )

        # Creates 3 campaigns
        assert get_campaign_data.call_args_list == [
            mock.call("Digital specialists", "096e52cebb", 'Digital Outcomes and Specialists 3'),
            mock.call("Digital outcomes", "096e52cebb", 'Digital Outcomes and Specialists 4'),
            mock.call("User research participants", "096e52cebb", 'Digital Outcomes and Specialists 4')
        ]
        assert self.dm_mailchimp_client.create_campaign.call_args_list == [
            mock.call({"created": "campaign"}),
            mock.call({"created": "campaign"}),
            mock.call({"created": "campaign"})
        ]

        # Sets campaign content
        assert get_html_content.call_args_list == [
            mock.call([BRIEF_1, BRIEF_2], 1),
            mock.call([BRIEF_3], 1),
            mock.call([BRIEF_4], 1),
        ]
        assert self.dm_mailchimp_client.set_campaign_content.call_args_list == [
            mock.call("1", {"first": "content"}),
            mock.call("1", {"first": "content"}),
            mock.call("1", {"first": "content"})
        ]

        # Sends campaign
        assert self.dm_mailchimp_client.send_campaign.call_args_list == [
            mock.call("1"),
            mock.call("1"),
            mock.call("1")
        ]

    def test_main_gets_live_briefs_for_one_day_by_default(self, get_live_briefs_by_framework_and_lot):
        with freeze_time('2017-04-19 08:00:00'):
            main(
                self.data_api_client,
                self.dm_mailchimp_client,
                1,
                framework_override=None,
                list_id_override=None,
                lot_slug_override=None
            )
        assert get_live_briefs_by_framework_and_lot.call_args_list == [
            mock.call(mock.ANY, date(2017, 4, 18), date(2017, 4, 18))
        ]

    def test_main_can_get_live_briefs_for_three_days(self, get_live_briefs_by_framework_and_lot):
        with freeze_time('2017-04-10 08:00:00'):
            main(
                self.data_api_client,
                self.dm_mailchimp_client,
                number_of_days=3,
                framework_override=None,
                list_id_override=None,
                lot_slug_override=None
            )
        assert get_live_briefs_by_framework_and_lot.call_args_list == [
            mock.call(mock.ANY, date(2017, 4, 7), date(2017, 4, 9))
        ]

    @mock.patch('dmscripts.send_dos_opportunities_email.get_html_content', autospec=True)
    @mock.patch('dmscripts.send_dos_opportunities_email.get_campaign_data', autospec=True)
    def test_override_framework_only_sends_for_that_framework(
            self, get_campaign_data, get_html_content, get_live_briefs_by_framework_and_lot):
        get_live_briefs_by_framework_and_lot.return_value = {
            'digital-outcomes-and-specialists-3': {
                'digital-specialists': [BRIEF_1, BRIEF_2]
            },
            'digital-outcomes-and-specialists-4': {
                'digital-outcomes': [BRIEF_3],
                'user-research-participants': [BRIEF_4],
            }
        }
        get_campaign_data.return_value = {"created": "campaign"}
        get_html_content.return_value = {"first": "content"}
        self.dm_mailchimp_client.create_campaign.return_value = "1"

        assert main(
            self.data_api_client,
            self.dm_mailchimp_client,
            1,
            framework_override="digital-outcomes-and-specialists-3",
            list_id_override="096e52cebb",
            lot_slug_override=None
        )

        # Creates 1 campaign for Briefs 1 and 2
        assert get_campaign_data.call_args_list == [
            mock.call("Digital specialists", "096e52cebb", 'Digital Outcomes and Specialists 3'),
        ]
        assert get_html_content.call_args_list == [mock.call([BRIEF_1, BRIEF_2], 1)]

    @mock.patch('dmscripts.send_dos_opportunities_email.get_html_content', autospec=True)
    @mock.patch('dmscripts.send_dos_opportunities_email.get_campaign_data', autospec=True)
    def test_override_lot_only_sends_for_that_lot(
            self, get_campaign_data, get_html_content, get_live_briefs_by_framework_and_lot):
        get_live_briefs_by_framework_and_lot.return_value = {
            'digital-outcomes-and-specialists-3': {
                'digital-specialists': [BRIEF_1, BRIEF_2]
            },
            'digital-outcomes-and-specialists-4': {
                'digital-outcomes': [BRIEF_3],
                'user-research-participants': [BRIEF_4],
            }
        }
        get_campaign_data.return_value = {"created": "campaign"}
        get_html_content.return_value = {"first": "content"}
        self.dm_mailchimp_client.create_campaign.return_value = "1"

        assert main(
            self.data_api_client,
            self.dm_mailchimp_client,
            1,
            framework_override=None,
            list_id_override="096e52cebb",
            lot_slug_override='digital-outcomes'
        )

        # Creates 1 campaign for Brief 3
        assert get_campaign_data.call_args_list == [
            mock.call("Digital outcomes", "096e52cebb", 'Digital Outcomes and Specialists 4'),
        ]
        assert get_html_content.call_args_list == [mock.call([BRIEF_3], 1)]

    @mock.patch('dmscripts.send_dos_opportunities_email.logger', autospec=True)
    def test_if_no_briefs_then_no_campaign_created_nor_sent(self, logger, get_live_briefs_by_framework_and_lot):
        get_live_briefs_by_framework_and_lot.return_value = {}

        with freeze_time('2017-04-10 08:00:00'):
            result = main(
                self.data_api_client,
                self.dm_mailchimp_client,
                number_of_days=3,
                framework_override=None,
                list_id_override=None,
                lot_slug_override=None
            )

        assert result is True
        assert self.dm_mailchimp_client.create_campaign.call_count == 0
        assert self.dm_mailchimp_client.set_campaign_content.call_count == 0
        assert self.dm_mailchimp_client.send_campaign.call_count == 0

        assert get_live_briefs_by_framework_and_lot.call_args_list == [
            mock.call(self.data_api_client, date(2017, 4, 7), date(2017, 4, 9))
        ]
        assert logger.info.call_args_list == [
            mock.call("No new briefs found for DOS frameworks in the last 3 day(s)", extra={"number_of_days": 3})
        ]
