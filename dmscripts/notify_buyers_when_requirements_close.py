# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

import dmapiclient
from dmutils.email import send_email
from dmutils.email.exceptions import EmailError
from dmutils.formats import DATE_FORMAT, DATETIME_FORMAT

from dmscripts.helpers.email_helpers import get_sent_emails
from . import logging

from .html import render_html

logger = logging.configure_logger({'dmapiclient': logging.INFO})


def get_closed_briefs(data_api_client, date_closed):
    return [
        brief for brief in data_api_client.find_briefs_iter(status='closed', with_users=True)
        if datetime.strptime(brief['applicationsClosedAt'], DATETIME_FORMAT).date() == date_closed
    ]


def notify_users(email_api_key, brief):
    logger.info("Notifying users about brief ID: {brief_id} - '{brief_title}'",
                extra={'brief_title': brief['title'], 'brief_id': brief['id']})
    for user in brief['users']:
        try:
            email_body = render_html('email_templates/requirements_closed.html', data={
                'brief_id': brief['id'],
                'brief_title': brief['title'],
                'lot_slug': brief['lotSlug'],
                'framework_slug': brief['frameworkSlug']
            })
            send_email(
                [user['emailAddress'] for user in brief['users'] if user['active']],
                email_body,
                email_api_key,
                u'Next steps for your ‘{}’ requirements'.format(brief['title']),
                'enquiries@digitalmarketplace.service.gov.uk',
                'Digital Marketplace Admin',
                ['requirements-closed'],
                metadata={'brief_id': brief['id']},
                logger=logger
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


def get_notified_briefs(email_api_key, date_closed):
    return set(
        email['metadata']['brief_id']
        for email in get_sent_emails(email_api_key, ['requirements-closed'], date_from=date_closed.isoformat())
        if 'brief_id' in (email.get('metadata') or {})
    )


def main(data_api_url, data_api_access_token, email_api_key, date_closed, dry_run):
    logger.info("Data API URL: {data_api_url}", extra={'data_api_url': data_api_url})

    date_closed = get_date_closed(date_closed)
    if date_closed < (datetime.utcnow() - timedelta(days=8)).date():
        logger.error('Not allowed to notify about briefs that closed more than a week ago')
        return False

    data_api_client = dmapiclient.DataAPIClient(data_api_url, data_api_access_token)

    closed_briefs = get_closed_briefs(data_api_client, date_closed)
    if not closed_briefs:
        logger.info("No briefs closed on {date_closed}", extra={"date_closed": date_closed})
        return True

    logger.info("Notifying users about {briefs_count} closed briefs", extra={'briefs_count': len(closed_briefs)})

    notified_briefs = get_notified_briefs(email_api_key, date_closed)

    logger.info('Brief notifications sent since {date_closed}: {notified_briefs_count}',
                extra={'date_closed': date_closed, 'notified_briefs_count': len(notified_briefs)})

    for brief in closed_briefs:
        if brief['id'] in notified_briefs:
            logger.info('Brief notification already sent for brief ID: {brief_id}', extra={'brief_id': brief['id']})
        elif dry_run:
            logger.info("Would notify users about brief ID: {brief_id}", extra={'brief_id': brief['id']})
        else:
            status = notify_users(email_api_key, brief)
            if not status:
                return False

    return True
