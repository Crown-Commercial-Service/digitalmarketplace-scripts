"""Spike script into mail chimp email sending.

Test list ID is "096e52cebb" which can be used for local development
"""
from datetime import datetime

from mailchimp3 import MailChimp

from requests.exceptions import RequestException

from dmscripts.helpers.html_helpers import render_html
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging

logger = logging_helpers.configure_logger({'dmapiclient': logging.INFO})


lots = {
    "digital-specialists": {
        "lot_name": "Digital specialists",
        "list_id": "096e52cebb"
    },
    "digital-outcomes": {
        "lot_name": "Digital outcomes",
        "list_id": "096e52cebb"
    },
    "user-research-participants": {
        "lot_name": "User research participants",
        "list_id": "096e52cebb"
    }
}


def create_campaign_data(lot_name, list_id):
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


def get_html_content():
    email_body = render_html("email_templates/dos_opportunities.html", data={})
    return email_body


def create_campaign(mailchimp_client, campaign_data):
    try:
        campaign = mailchimp_client.campaigns.create(campaign_data)
        return campaign['id']
    except RequestException as e:
        logger.error(
            "Mailchimp failed to create campaign for '{0}'".format(
                campaign_data.get("settings").get("title")
            ),
            extra={"error": e.message}
        )
    return False


def set_campaign_content(mailchimp_client, campaign_id, content_data):
    try:
        return mailchimp_client.campaigns.content.update(campaign_id, content_data)
    except RequestException as e:
        logger.error(
            "Mailchimp failed to set content for campaign id '{0}'".format(campaign_id),
            extra={"error": e.message}
        )
    return False


def send_campaign(mailchimp_client, campaign_id):
    try:
        return client.campaigns.actions.send(campaign_id=campaign_id)
    except Exception as e:
        print e


def main(mailchimp_username, mailchimp_api_key):
    mailchimp_client = MailChimp(mailchimp_username, mailchimp_api_key)

    campaign_id = create_campaign(mailchimp_client)
    if not campaign_id:
        return False
    return True
