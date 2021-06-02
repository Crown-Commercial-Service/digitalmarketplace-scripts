from datetime import timedelta, datetime

from dmutils.formats import DATETIME_FORMAT


class MailchimpRemovalFailed(EnvironmentError):
    pass


def remove_user_from_mailchimp(dm_mailchimp_client, logger, user, dry_run=True):
    prefix = "[DRY RUN]: " if dry_run else ""

    email_hash = dm_mailchimp_client.get_email_hash(user["emailAddress"])
    logger.info(
        "Checking mailing list membership for email with hash %s (user %s)",
        email_hash,
        user["id"],
    )
    mailing_lists = dm_mailchimp_client.get_lists_for_email(user["emailAddress"])
    if mailing_lists:
        for mailing_list in mailing_lists:
            logger.warn(
                "%sRemoving email with hash %s from list %s ('%s')",
                prefix,
                email_hash,
                mailing_list["list_id"],
                mailing_list["name"],
            )
            if not dry_run:
                rm_result = dm_mailchimp_client.permanently_remove_email_from_list(
                    email_address=user["emailAddress"],
                    list_id=mailing_list["list_id"],
                )
                if not rm_result:
                    raise MailchimpRemovalFailed(
                        "Mailchimp failure trying to permanently_remove_email_from_list"
                    )


def remove_user_data(
    data_api_client,
    logger,
    user,
    dm_mailchimp_client=None,
    dry_run=True,
):
    prefix = "[DRY RUN]: " if dry_run else ""

    if dm_mailchimp_client is not None:
        remove_user_from_mailchimp(dm_mailchimp_client, logger, user, dry_run)

    logger.warn(f"{prefix}Removing personal data in API for user: {user['id']}")
    if not dry_run:
        data_api_client.remove_user_personal_data(
            user["id"], "Data Retention Script {}".format(datetime.now().isoformat())
        )


def data_retention_remove_user_data(
    data_api_client,
    logger,
    dm_mailchimp_client=None,
    dry_run=True,
):
    cutoff_date = datetime.now() - timedelta(days=365 * 3)

    for user in data_api_client.find_users_iter(personal_data_removed=False):
        last_logged_in_at = datetime.strptime(user["loggedInAt"], DATETIME_FORMAT)
        if last_logged_in_at < cutoff_date:
            remove_user_data(
                data_api_client, logger, user, dm_mailchimp_client, dry_run
            )
