from datetime import datetime, date, timedelta

from requests.exceptions import RequestException

from dmscripts.helpers.html_helpers import render_html
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging
from dmutils.formats import DATETIME_FORMAT

import dmapiclient

logger = logging_helpers.configure_logger({'dmapiclient': logging.INFO})


def get_live_briefs_between_two_dates(data_api_client, lot_slug, start_date, end_date):
    return [
        brief for brief in data_api_client.find_briefs_iter(status="live", lot=lot_slug)
        if datetime.strptime(brief['publishedAt'], DATETIME_FORMAT).date() >= start_date
        and datetime.strptime(brief['publishedAt'], DATETIME_FORMAT).date() <= end_date
    ]


def get_campaign_data(lot_name, list_id):
    return {
        "type": "regular",
        "recipients": {
            "list_id": list_id,
        },
        "settings": {
            "subject_line": "New opportunities for {0}: Digital Outcomes and Specialists 2".format(lot_name),
            "title": "DOS Suppliers: {0} [{1}]".format(lot_name, datetime.now().strftime("%d %B")),
            "from_name": "Digital Marketplace Team",
            "reply_to": "do-not-reply@digitalmarketplace.service.gov.uk",
            "use_conversation": False,
            "authenticate": True,
            "auto_footer": False,
            "inline_css": False,
            "auto_tweet": False,
            "fb_comments": False
        },
        "tracking": {
            "opens": True,
            "html_clicks": True,
            "text_clicks": False,
            "goal_tracking": False,
            "ecomm360": False
        }
    }


def get_html_content(briefs):
    # function not yet implemented
    html_content = render_html("email_templates/dos_opportunities.html", data={"briefs": briefs, "datetime": datetime, "dateformat": DATETIME_FORMAT})
    return {"html": html_content}


def create_campaign(mailchimp_client, campaign_data):
    try:
        campaign = mailchimp_client.campaigns.create(campaign_data)
        return campaign['id']
    except RequestException as e:
        logger.error(
            "Mailchimp failed to create campaign for '{0}'".format(
                campaign_data.get("settings").get("title")
            ),
            extra={"error": str(e)}
        )
    return False


def set_campaign_content(mailchimp_client, campaign_id, content_data):
    try:
        return mailchimp_client.campaigns.content.update(campaign_id, content_data)
    except RequestException as e:
        logger.error(
            "Mailchimp failed to set content for campaign id '{0}'".format(campaign_id),
            extra={"error": str(e)}
        )
    return False


def send_campaign(mailchimp_client, campaign_id):
    try:
        mailchimp_client.campaigns.actions.send(campaign_id)
        return True
    except RequestException as e:
        logger.error(
            "Mailchimp failed to send campaign id '{0}'".format(campaign_id),
            extra={"error": str(e)}
        )
    return False


def main(data_api_client, mailchimp_client, lot_data, number_of_days):
    logger.info(
        "Begin process to send DOS notification emails for '{0}' lot".format(lot_data["lot_slug"]),
        extra={"lot_data": lot_data, "number_of_days": number_of_days}
    )

    start_date = date.today() - timedelta(days=number_of_days)
    end_date = date.today() - timedelta(days=1)

    live_briefs = get_live_briefs_between_two_dates(data_api_client, lot_data["lot_slug"], start_date, end_date)
    if not live_briefs:
        logger.info(
            "No new briefs found for '{0}' lot".format(lot_data["lot_slug"]),
            extra={"number_of_days": number_of_days}
        )
        return True
    logger.info(
        "{0} new briefs found for '{1}' lot".format(len(live_briefs), lot_data["lot_slug"])
    )

    campaign_data = get_campaign_data(lot_data["lot_name"], lot_data["list_id"])
    logger.info(
        "Creating campaign for '{0}' lot".format(lot_data["lot_slug"])
    )
    campaign_id = create_campaign(mailchimp_client, campaign_data)
    if not campaign_id:
        return False

    content_data = get_html_content()
    logger.info(
        "Setting campaign data for '{0}' lot and '{1}' campaign id".format(lot_data["lot_slug"], campaign_id)
    )
    if not set_campaign_content(mailchimp_client, campaign_id, content_data):
        return False

    logger.info(
        "Sending campaign for '{0}' lot and '{1}' campaign id".format(lot_data["lot_slug"], campaign_id)
    )
    if not send_campaign(mailchimp_client, campaign_id):
        return False

    return True
