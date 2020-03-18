from datetime import date
from itertools import chain
from logging import Logger
from typing import Optional
from uuid import UUID, uuid4
from warnings import warn

from dmapiclient import DataAPIClient

from dmutils.email import DMNotifyClient
from dmutils.email.exceptions import EmailError
from dmutils.email.helpers import hash_string
from dmutils.env_helpers import get_web_url_from_stage
from dmutils import formats


_date_formats = (
    "displaytimeformat",
    "dateformat",
    "datetimeformat",
)


def _maybe_time_today(key, iso_timestamp):
    """
    If the given timestamp matches today's local date and is hour-exact, return an additional sequence containing
    a `_timetoday` string for this timestamp
    """
    localized_dt = formats.get_localized_datetime(iso_timestamp)
    if localized_dt.date() == date.today():
        if localized_dt.minute == localized_dt.second == localized_dt.microsecond == 0:
            return ((
                f"{key}_timetoday",
                f'Today at {localized_dt.strftime("%I%p %Z").replace("AM", "am").replace("PM", "pm").lstrip("0")}',
            ),)

        warn(f"Not emitting {key}_timetoday because timestamp is not hour-exact: {iso_timestamp!r}")

    # omit this piece of context, if used with any template which requires it, the notify call should
    # result in an error, hopefully alerting the user to the problem (i.e. it's the wrong day or the timestamp
    # isn't appropriate)
    return ()


def _formatted_dates_from_framework(framework):
    return dict(chain.from_iterable(
        chain(
            (
                (f"{key[:-3]}_{date_format}", getattr(formats, date_format)(iso_timestamp),)
                for date_format in _date_formats
            ),
            _maybe_time_today(key[:-3], iso_timestamp),
        ) for key, iso_timestamp in framework.items() if key.endswith("UTC")
    ))


def notify_suppliers_of_framework_application_event(
    data_api_client: DataAPIClient,
    notify_client: DMNotifyClient,
    notify_template_id: str,
    framework_slug: str,
    stage: str,
    dry_run: bool,
    logger: Logger,
    run_id: Optional[UUID] = None,
) -> int:
    run_is_new = not run_id
    run_id = run_id or uuid4()
    logger.info(f"{'Starting' if run_is_new else 'Resuming'} run id {{run_id}}", extra={"run_id": str(run_id)})

    framework = data_api_client.get_framework(framework_slug)["frameworks"]
    framework_context = {
        "framework_name": framework["name"],
        "updates_url": f"{get_web_url_from_stage(stage)}/suppliers/frameworks/{framework['slug']}/updates",
        "framework_dashboard_url": f"{get_web_url_from_stage(stage)}/suppliers/frameworks/{framework['slug']}/",
        "clarification_questions_closed": "no" if framework["clarificationQuestionsOpen"] else "yes",
        **_formatted_dates_from_framework(framework),
    }

    failure_count = 0

    for supplier_framework in data_api_client.find_framework_suppliers_iter(framework_slug):
        for user in data_api_client.find_users_iter(supplier_id=supplier_framework["supplierId"]):
            if user["active"]:
                # generating ref separately so we can exclude certain parameters from the context dict
                notify_ref = notify_client.get_reference(
                    user["emailAddress"],
                    notify_template_id,
                    {
                        "framework_slug": framework["slug"],
                        "run_id": str(run_id),
                    },
                )
                if dry_run:
                    if notify_client.has_been_sent(notify_ref):
                        logger.debug(
                            "[DRY RUN] Would NOT send notification to {email_hash} (already sent)",
                            extra={"email_hash": hash_string(user["emailAddress"])},
                        )
                    else:
                        logger.info(
                            "[DRY RUN] Would send notification to {email_hash}",
                            extra={"email_hash": hash_string(user["emailAddress"])},
                        )
                else:
                    try:
                        notify_client.send_email(
                            user["emailAddress"],
                            notify_template_id,
                            framework_context,
                            allow_resend=False,
                            reference=notify_ref,
                        )
                    except EmailError as e:
                        failure_count += 1
                        logger.error(
                            "Failed sending to {email_hash}: {e}",
                            extra={
                                "email_hash": hash_string(user["emailAddress"]),
                                "e": str(e),
                            },
                        )

    return failure_count
