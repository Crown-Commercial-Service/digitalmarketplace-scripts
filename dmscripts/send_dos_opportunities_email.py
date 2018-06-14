from datetime import datetime, date, timedelta

from dmscripts.helpers.html_helpers import render_html
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging
from dmutils.formats import DATETIME_FORMAT, DISPLAY_DATE_FORMAT


logger = logging_helpers.configure_logger({'dmapiclient': logging.INFO})


def get_live_briefs_between_two_dates(data_api_client, lot_slug, start_date, end_date):
    """Get all briefs for a lot which were published between 2 dates."""
    return [
        brief for brief in data_api_client.find_briefs_iter(status="live", lot=lot_slug, human=True)
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


def get_html_content(briefs, number_of_days):
    start_date = date.today() - timedelta(days=number_of_days)

    for brief in briefs:
        brief.update(
            {"applicationsClosedAtDateTime": datetime.strptime(brief["applicationsClosedAt"], DATETIME_FORMAT)}
        )

    html_content = render_html("templates/email/dos_opportunities.html", data={
        "briefs": briefs,
        "today": datetime.today(),
        "display_date_format": DISPLAY_DATE_FORMAT,
        "number_of_days": number_of_days,
        "start_date": start_date
    })
    return {"html": html_content}


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
    campaign_id = mailchimp_client.create_campaign(campaign_data)
    if not campaign_id:
        return False

    content_data = get_html_content(live_briefs, number_of_days)
    logger.info(
        "Setting campaign data for '{0}' lot and '{1}' campaign id".format(lot_data["lot_slug"], campaign_id)
    )
    if not mailchimp_client.set_campaign_content(campaign_id, content_data):
        return False

    logger.info(
        "Sending campaign for '{0}' lot and '{1}' campaign id".format(lot_data["lot_slug"], campaign_id)
    )
    if not mailchimp_client.send_campaign(campaign_id):
        return False

    return True
