# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta

import dmapiclient
from dmutils.email.dm_notify import DMNotifyClient
from dmutils.email.exceptions import EmailError
from dmutils.formats import DATE_FORMAT

from dmscripts.helpers import logging_helpers, date_helpers, brief_data_helpers
from dmscripts.helpers.logging_helpers import logging

logger = logging_helpers.configure_logger({'dmapiclient': logging.INFO})


def notify_users(notify_client, notify_template_id, brief, user_id_list):
    failed_users = []
    if brief['users']:
        context_data = {
            'brief_id': brief['id'],
            'brief_title': brief['title']
        }
        # Filter the brief's users by restricted user ID list if present
        brief_users = filter(lambda user: user['id'] in user_id_list, brief['users']) if user_id_list else brief['users']

        for user in brief_users:
            if user['active']:
                try:
                    notify_client.send_email(
                        user['emailAddress'], notify_template_id, context_data, allow_resend=False
                    )
                except EmailError:
                    failed_users.append(user['id'])

    return failed_users


# TODO: make sure we definitely don't need this!
def get_notified_briefs(email_api_key, date_closed):
    return []


def main(
    data_api_url, data_api_access_token, notify_api_key, notify_template_id, date_closed, dry_run, user_id_list=None
):
    """
    Send emails to buyers via Notify, reminding them to award their closed briefs
    """
    logger.info("Data API URL: {data_api_url}", extra={'data_api_url': data_api_url})

    # TODO: Check that user has not already been emailed about this brief (in this timeframe)
    # TODO: enable the script to be repeated 4 weeks later (8 weeks after closing)

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

    # If user list supplied, check that the briefs have at least one user in the list
    if user_id_list:
        filtered_briefs = [
            brief for brief in closed_briefs if any(filter(lambda user: user['id'] in user_id_list, brief['users']))
        ]
        closed_briefs = filtered_briefs

    logger.info("Notifying users about {briefs_count} closed brief(s)", extra={'briefs_count': len(closed_briefs)})

    failed_users_for_each_brief = {}
    all_failed_users = []
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
            failed_users = notify_users(notify_client, notify_template_id, brief, user_id_list)
            if failed_users:
                failed_users_for_each_brief[brief['id']] = failed_users
                all_failed_users.extend(failed_users)

    if failed_users_for_each_brief:
        for brief_id, failed_brief_users in failed_users_for_each_brief.items():
            logger.error(
                'Email sending failed for the following buyer users of brief ID {brief_id}: {buyer_ids}',
                extra={"brief_id": brief_id, "buyer_ids": ",".join(map(str, failed_brief_users))}
            )
        logger.error('All failures for award closed briefs notification '
                     'on closing date {date_closed}: {all_failed_users}',
                     extra={"date_closed": date_closed.strftime(DATE_FORMAT),
                            "all_failed_users": ",".join(map(str, all_failed_users))}
                     )
        return False
    return True
