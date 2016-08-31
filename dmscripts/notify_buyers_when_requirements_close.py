# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

import dmapiclient
from dmutils.formats import DATE_FORMAT, DATETIME_FORMAT
from dmutils.email import send_email, MandrillException

from .email import get_sent_emails
from .html import render_html

from . import logging

logger = logging.configure_logger({'dmapiclient': logging.INFO})


def get_closed_briefs(data_api_client, closed_at):
    return [
        brief for brief in data_api_client.find_briefs_iter(status='closed', with_users=True)
        if datetime.strptime(brief['applicationsClosedAt'], DATETIME_FORMAT).date() == closed_at
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
        except MandrillException as e:
            logger.error(
                "Email failed to send for brief_id: {brief_id}",
                extra={'error': e, 'brief_id': brief['id']}
            )

            return False


def get_closed_at(closed_at):
    if closed_at is None:
        return (datetime.utcnow() - timedelta(days=1)).date()
    else:
        return datetime.strptime(closed_at, DATE_FORMAT).date()


def get_notified_briefs(email_api_key, closed_at):
    return set(
        email['metadata']['brief_id']
        for email in get_sent_emails(email_api_key, ['requirements-closed'], date_from=closed_at.isoformat())
        if 'brief_id' in (email.get('metadata') or {})
    )


def main(data_api_url, data_api_access_token, email_api_key, closed_at, dry_run):
    logger.info("Data API URL: {data_api_url}", extra={'data_api_url': data_api_url})

    closed_at = get_closed_at(closed_at)
    if closed_at < (datetime.utcnow() - timedelta(days=8)).date():
        logger.error('Not allowed to notify about briefs that closed more than a week ago')
        return False

    data_api_client = dmapiclient.DataAPIClient(data_api_url, data_api_access_token)

    closed_briefs = get_closed_briefs(data_api_client, closed_at)
    if not closed_briefs:
        logger.info("No briefs closed on {closed_at}", extra={"closed_at": closed_at})
        return True

    logger.info("Notifying users about {briefs_count} closed briefs", extra={'briefs_count': len(closed_briefs)})

    notified_briefs = get_notified_briefs(email_api_key, closed_at)

    logger.info('Brief notifications sent since {closed_at}: {notified_briefs_count}',
                extra={'closed_at': closed_at, 'notified_briefs_count': len(notified_briefs)})

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
