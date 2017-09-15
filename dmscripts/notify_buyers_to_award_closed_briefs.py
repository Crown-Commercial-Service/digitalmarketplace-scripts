# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta

import dmapiclient
from dmutils.email.dm_notify import DMNotifyClient
from dmutils.email.exceptions import EmailError

from dmscripts.helpers import logging_helpers, date_helpers, brief_data_helpers
from dmscripts.helpers.logging_helpers import logging

logger = logging_helpers.configure_logger({'dmapiclient': logging.INFO})


def notify_users(notify_client, notify_template_id, brief):
    failed_users = []
    if brief['users']:
        context_data = {
            'brief_id': brief['id'],
            'brief_title': brief['title']
        }
        for user in brief['users']:
            if user['active']:
                try:
                    notify_client.send_email(
                        user['emailAddress'], notify_template_id, context_data, allow_resend=False
                    )
                except EmailError:
                    failed_users.append(user['emailAddress'])

    return failed_users


# TODO: make sure we definitely don't need this!
def get_notified_briefs(email_api_key, date_closed):
    return []


def main(data_api_url, data_api_access_token, notify_api_key, notify_template_id, date_closed, dry_run):
    """
    Send emails to buyers via Notify, reminding them to award their closed briefs
    """
    logger.info("Data API URL: {data_api_url}", extra={'data_api_url': data_api_url})

    # TODO: Check that user has not already been emailed about this brief (in this timeframe)
    # TODO: accept optional 'failed-users' 'failed-briefs' kwargs for retrying script (filter the usual brief query)
    # TODO: enable the script to be repeated 4 weeks later (8 weeks after closing)

    # Log failures
    if date_closed:
        date_closed = date_helpers.get_date_closed(date_closed)
        if date_closed > (datetime.utcnow() - timedelta(days=28)).date():
            logger.error('Not allowed to notify about briefs that closed less than 4 weeks ago')
            return False
    else:
        date_closed = date.today() - timedelta(days=28)

    data_api_client = dmapiclient.DataAPIClient(data_api_url, data_api_access_token)
    if not dry_run:
        notify_client = DMNotifyClient(notify_api_key, logger=logger)

    closed_briefs = brief_data_helpers.get_closed_briefs(data_api_client, date_closed)
    if not closed_briefs:
        logger.info("No briefs closed on {date_closed}", extra={"date_closed": date_closed})
        return True

    logger.info("Notifying users about {briefs_count} closed briefs", extra={'briefs_count': len(closed_briefs)})

    failed_users_for_each_brief = {}
    for brief in closed_briefs:
        if dry_run:
            logger.info(
                "Would notify {no_of_users} user(s) about brief ID: {brief_id} - '{brief_title}'",
                extra={'no_of_users': len(brief['users']), 'brief_id': brief['id'], 'brief_title': brief['title']}
            )
        else:
            logger.info("Notifying {no_of_users} user(s) about brief ID: {brief_id} - '{brief_title}'",
                        extra={
                            'brief_title': brief['title'],
                            'brief_id': brief['id'],
                            'no_of_users': len(brief['users']),
                        })
            failed_users = notify_users(notify_client, notify_template_id, brief)
            if failed_users:
                failed_users_for_each_brief[brief['id']] = failed_users

    if failed_users_for_each_brief:
        logger.info('TODO: how are we going to log/resend these failures')
        return False
    return True
