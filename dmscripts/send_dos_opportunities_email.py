from datetime import datetime, date, timedelta

from dmscripts.helpers.html_helpers import render_html
from dmscripts.helpers.logging_helpers import logging
from dmutils.formats import DATETIME_FORMAT, DISPLAY_DATE_FORMAT


logger = logging.getLogger('script')


MAILCHIMP_LIST_IDS = {
    'digital-outcomes-and-specialists': {
        'digital-specialists': None,
        'digital-outcomes': None,
        'user-research-participants': None,
    },
    'digital-outcomes-and-specialists-2': {
        'digital-specialists': "30ba9fdf39",
        'digital-outcomes': "97952fee38",
        'user-research-participants': "e6b93a3bce",
    },
    'digital-outcomes-and-specialists-3': {
        'digital-specialists': "bee802d641",
        'digital-outcomes': "5c92c78a78",
        'user-research-participants': "34ebe0bffa",
    },
    'digital-outcomes-and-specialists-4': {
        'digital-specialists': "29d06d5201",
        'digital-outcomes': "4360debc5a",
        'user-research-participants': "2538f8a0f1",
    }
}

LOT_NAMES = {
    "digital-specialists": "Digital specialists",
    "digital-outcomes": "Digital outcomes",
    "user-research-participants": "User research participants",
}


def get_live_briefs_between_two_dates(data_api_client, start_date, end_date):
    """Get all briefs which were published between 2 dates."""
    return [
        brief for brief in data_api_client.find_briefs_iter(status="live", human=True)
        if datetime.strptime(brief['publishedAt'], DATETIME_FORMAT).date() >= start_date
        and datetime.strptime(brief['publishedAt'], DATETIME_FORMAT).date() <= end_date
    ]


def get_campaign_data(lot_name, list_id, framework_name):
    return {
        "type": "regular",
        "recipients": {
            "list_id": list_id,
        },
        "settings": {
            "subject_line": "New opportunities for {0}: {1}".format(
                lot_name, framework_name
            ),
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
            "opens": False,
            "html_clicks": False,
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


def get_live_briefs_by_framework_and_lot(client, start_date, end_date):
    """
    Create a map of all live briefs, organised by framework and lot.
    A framework/lot will only be included if there are live briefs for it in the time range given.

    :param client: Data API client
    :param start_date: YYYY-MM-DD
    :param end_date: YYYY-MM-DD
    :return: dict of live briefs, e.g.
        {
            'digital-outcomes-and-specialists-2': {
                'digital-outcomes': [brief1, brief2, ...],
                'user-research-participants': [brief3]
            },
            'digital-outcomes-and-specialists-3': {
                'digital-specialists': [brief4, brief5],
                'digital-outcomes': [brief6, brief7]
            }
        }
    """
    briefs = get_live_briefs_between_two_dates(client, start_date, end_date)
    briefs_by_fw_and_lot = {}

    for brief in briefs:
        brief_fw_slug = brief['frameworkSlug']
        brief_lot_slug = brief['lotSlug']
        if brief['frameworkSlug'] in briefs_by_fw_and_lot:
            if brief_lot_slug in briefs_by_fw_and_lot[brief_fw_slug]:
                briefs_by_fw_and_lot[brief_fw_slug][brief_lot_slug].append(brief)
            else:
                briefs_by_fw_and_lot[brief_fw_slug][brief_lot_slug] = [brief]
        else:
            briefs_by_fw_and_lot[brief_fw_slug] = {
                brief_lot_slug: [brief]
            }
    return briefs_by_fw_and_lot


def main(
    data_api_client,
    mailchimp_client,
    number_of_days,
    *,
    framework_override=None,
    list_id_override=None,
    lot_slug_override=None
):
    """
    Default behaviour is to fetch any briefs (regardless of framework/lot) published in the last N days.

    The script groups briefs by framework/lot, and for each combination, looks up the Mailchimp list ID, and creates &
    sends a new campaign.
    - If a framework_override is supplied, just find briefs for that framework
    - If a lot_override is supplied, just find briefs for that lot
    - If a list_id_override is supplied, only send emails to that list ID regardless of lot/framework

    For most of the year, there should only be one framework iteration with live briefs. However during the transition
    period between DOS framework iterations, we need to support both iterations.

    For example, on the second day of DOS4, any DOS3 briefs created the first day (before the go-live switchover) will
    still need to be emailed to DOS3 suppliers, as well as the usual DOS4 briefs sent to DOS4 suppliers.
    """
    start_date = date.today() - timedelta(days=number_of_days)
    end_date = date.today() - timedelta(days=1)

    # Get all live briefs for each DOS framework on the lot (or a single DOS framework, if supplied as a script arg)
    live_briefs_by_framework = get_live_briefs_by_framework_and_lot(data_api_client, start_date, end_date)

    # If specific framework script arg supplied, ignore other frameworks
    if framework_override:
        if not live_briefs_by_framework.get(framework_override):
            logger.info(f"No new briefs found for {framework_override} in the last {number_of_days} day(s)")
            return True
        live_briefs_by_framework = {framework_override: live_briefs_by_framework.get(framework_override)}

    # If no briefs found, exit early
    if not live_briefs_by_framework:
        logger.info(f"No new briefs found for DOS frameworks in the last {number_of_days} day(s)")
        return True

    for framework_slug in live_briefs_by_framework.keys():
        for lot_slug, live_briefs in live_briefs_by_framework[framework_slug].items():

            if lot_slug_override and lot_slug != lot_slug_override:
                logger.info(f"Skipping campaign for '{lot_slug}' lot on {framework_slug}")
                continue

            logger.info(f"{len(live_briefs)} new briefs found for '{lot_slug}' lot on {framework_slug}")

            # Get the list_id for this lot/framework combination (or use list ID override if supplied as script arg)
            list_id = list_id_override or MAILCHIMP_LIST_IDS[framework_slug][lot_slug]

            # Create a new campaign for today's emails
            logger.info(f"Creating campaign for '{lot_slug}' lot on {framework_slug}")
            campaign_data = get_campaign_data(LOT_NAMES[lot_slug], list_id, live_briefs[0]['frameworkName'])
            campaign_id = mailchimp_client.create_campaign(campaign_data)
            if not campaign_id:
                logger.warning(f"Unable to create campaign for '{lot_slug}' lot on {framework_slug}")
                continue

            # Build the email content
            content_data = get_html_content(live_briefs, number_of_days)
            logger.info(
                f"Setting campaign data for '{framework_slug}' framework, "
                f"'{lot_slug}' lot and '{campaign_id}' campaign id"
            )
            if not mailchimp_client.set_campaign_content(campaign_id, content_data):
                logger.warning(f"Unable to set campaign data for campaign id '{campaign_id}'")
                continue

            # Send the emails
            logger.info(
                f"Sending campaign for '{framework_slug}' framework, '{lot_slug}' lot and '{campaign_id}' campaign id"
            )
            if not mailchimp_client.send_campaign(campaign_id):
                logger.warning(f"Unable to send campaign for campaign id '{campaign_id}'")
                continue

    return True
