# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

import dmapiclient
from dmutils.email.dm_notify import DMNotifyClient
from dmutils.email.exceptions import EmailError
from dmutils.env_helpers import get_web_url_from_stage
from dmutils.formats import DATE_FORMAT

from dmscripts.helpers.brief_data_helpers import get_briefs_closed_on_date
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging


EMAIL_TEMPLATE_ID = "c1f88c6f-1c6f-4f50-b52b-947bcea5e6c1"

logger = logging_helpers.configure_logger({'dmapiclient': logging.INFO})


def notify_users(email_api_key, stage, brief):
    logger.info("Notifying users about brief ID: {brief_id} - '{brief_title}'",
                extra={'brief_title': brief['title'], 'brief_id': brief['id']})
    email_client = DMNotifyClient(email_api_key, logger=logger)
    if brief['users']:
        try:
            brief_responses_url = \
                "{base_url}/buyers/frameworks/{framework_slug}/requirements/{lot_slug}/{brief_id}/responses".format(
                    base_url=get_web_url_from_stage(stage),
                    brief_id=brief["id"],
                    brief_title=brief["title"],
                    lot_slug=brief["lotSlug"],
                    framework_slug=brief["frameworkSlug"],
                )
            for email_address in (user['emailAddress'] for user in brief['users'] if user['active']):
                email_client.send_email(
                    email_address,
                    template_name_or_id=EMAIL_TEMPLATE_ID,
                    personalisation={
                        "brief_title": brief["title"],
                        "brief_responses_url": brief_responses_url,
                    },
                    allow_resend=False,
                )

            return True
        except EmailError as e:
            logger.error(
                "Email failed to send for brief_id: {brief_id}",
                extra={'error': e, 'brief_id': brief['id']}
            )

            return False


def get_date_closed(date_closed):
    if date_closed is None:
        return (datetime.utcnow() - timedelta(days=1)).date()
    else:
        return datetime.strptime(date_closed, DATE_FORMAT).date()


def main(data_api_url, data_api_access_token, email_api_key, stage, date_closed, dry_run):
    date_closed = get_date_closed(date_closed)
    if date_closed < (datetime.utcnow() - timedelta(days=8)).date():
        logger.error('Not allowed to notify about briefs that closed more than a week ago')
        return False

    data_api_client = dmapiclient.DataAPIClient(data_api_url, data_api_access_token)

    closed_briefs = get_briefs_closed_on_date(data_api_client, date_closed)
    if not closed_briefs:
        logger.info("No briefs closed on {date_closed}", extra={"date_closed": date_closed})
        return True

    logger.info("Notifying users about {briefs_count} closed briefs", extra={'briefs_count': len(closed_briefs)})

    for brief in closed_briefs:
        if dry_run:
            logger.info("Would notify users about brief ID: {brief_id}", extra={'brief_id': brief['id']})
        else:
            status = notify_users(email_api_key, stage, brief)
            if not status:
                return False

    return True
