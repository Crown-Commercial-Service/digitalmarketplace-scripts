# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta

import dmapiclient
from dmutils.email import DMNotifyClient
from dmutils.email.exceptions import EmailError
from dmutils.formats import DATE_FORMAT

from dmscripts.helpers import logging_helpers, date_helpers, brief_data_helpers

logger = logging_helpers.configure_logger({'dmapiclient': logging_helpers.logging.INFO})


def _filter_brief_users_by_optional_user_id_list(brief, user_id_list):
    """Filter the brief's users by restricted user ID list if present"""
    if user_id_list:
        return filter(lambda user: user['id'] in user_id_list, brief['users'])
    else:
        return brief['users']


def _filter_briefs_by_user_id_list(briefs, user_id_list):
    """Return a list of briefs if they have at least 1 user in the given ID list"""
    return [brief for brief in briefs if any(_filter_brief_users_by_optional_user_id_list(brief, user_id_list))]


def _create_context_for_brief(brief):
    return {
        'brief_id': brief['id'],
        'brief_title': brief['title'],
        'framework_slug': brief['frameworkSlug'],
        'lot_slug': brief['lotSlug'],
        'utm_date': date.today().strftime("%Y%m%d")
    }


def notify_users(notify_client, notify_template_id, brief, user_id_list):
    failed_users = []

    context_data = _create_context_for_brief(brief)
    brief_users = _filter_brief_users_by_optional_user_id_list(brief, user_id_list)

    for user in brief_users:
        if user['active']:
            try:
                notify_client.send_email(
                    user['emailAddress'], notify_template_id, context_data, allow_resend=False
                )
            except EmailError:
                failed_users.append(user['id'])

    return failed_users


def _get_brief_closing_date(offset_days, closing_date_arg=None):
    """Returns the closing date object we will query briefs by.
    If no <closing_date_arg> is supplied, use '<offset_days> ago' as the date.

    If the <closing_date_arg> string is supplied, then check it's not less than <offset_days> ago
     (otherwise we'll email the buyers too soon after the closing date).
     e.g. On the 29th Jan, closing_date_arg=2016-01-01 offset_days=28 will return date(2016, 1, 1)
          On the 28th Jan, closing_date_arg=2016-01-01 offset_days=28 will return False
    """
    if closing_date_arg:
        closing_date = date_helpers.get_date_closed(closing_date_arg)
        if closing_date > (datetime.utcnow() - timedelta(days=offset_days)).date():
            return False
        return closing_date
    return date.today() - timedelta(days=offset_days)


def main(
    data_api_url, data_api_access_token, notify_api_key, notify_template_id, offset_days,
    dry_run=None, date_closed=None, user_id_list=None
):
    """
    Send emails to buyers via Notify, reminding them to award their closed briefs

    offset_days:    send emails for briefs that closed X days ago
    dry_run:        log instead of sending emails
    date_closed:    if supplied, send emails for briefs that closed on this date
    user_id_list:   if supplied, only send emails to buyers with these user IDs
    """
    logger.info("Data API URL: {data_api_url}", extra={'data_api_url': data_api_url})

    date_closed = _get_brief_closing_date(offset_days, date_closed)
    if not date_closed:
        logger.error('Not allowed to notify about briefs that closed less than {} days ago', offset_days)
        return False

    data_api_client = dmapiclient.DataAPIClient(data_api_url, data_api_access_token)
    notify_client = DMNotifyClient(notify_api_key, logger=logger)

    closed_briefs = brief_data_helpers.get_briefs_closed_on_date(data_api_client, date_closed)
    if not closed_briefs:
        logger.info("No briefs closed on {date_closed}", extra={"date_closed": date_closed})
        return True

    # If user list supplied, only continue for briefs that have at least one user in that list
    if user_id_list:
        closed_briefs = _filter_briefs_by_user_id_list(closed_briefs, user_id_list)

    logger.info("Notifying users about {briefs_count} closed brief(s)", extra={'briefs_count': len(closed_briefs)})

    failed_users_for_each_brief = {}
    all_failed_users = []
    for brief in closed_briefs:
        logging_context = {
            'brief_title': brief['title'],
            'brief_id': brief['id'],
            'no_of_users': len(brief['users']),
        }
        if dry_run:
            logger.info(
                "Would notify {no_of_users} user(s) about brief ID: {brief_id} - '{brief_title}'",
                extra=logging_context
            )
        else:
            logger.info(
                "Notifying {no_of_users} user(s) about brief ID: {brief_id} - '{brief_title}'",
                extra=logging_context
            )
            failed_users = notify_users(notify_client, notify_template_id, brief, user_id_list)
            if failed_users:
                failed_users_for_each_brief[brief['id']] = failed_users
                all_failed_users.extend(failed_users)

    if failed_users_for_each_brief:
        for brief_id, failed_brief_users in sorted(failed_users_for_each_brief.items()):
            logger.error(
                'Email sending failed for the following buyer users of brief ID {brief_id}: {buyer_ids}',
                extra={
                    "brief_id": brief_id,
                    "buyer_ids": ",".join(map(str, failed_brief_users))
                }
            )

        logger.error(
            'All failures for award closed briefs notification on closing date {date_closed}: {all_failed_users}',
            extra={
                "date_closed": date_closed.strftime(DATE_FORMAT),
                "all_failed_users": ",".join(map(str, all_failed_users))
            }
        )
        return False
    return True
