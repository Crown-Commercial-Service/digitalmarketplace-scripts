from logging import Logger
from typing import Optional
from uuid import UUID, uuid4

from dmapiclient import DataAPIClient

from dmutils.email import DMNotifyClient
from dmutils.email.exceptions import EmailError
from dmutils.email.helpers import hash_string
from dmutils.env_helpers import get_web_url_from_stage


def notify_suppliers_of_new_fw_cq_answers(
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

    if framework["status"] != "open":
        raise ValueError(f"Framework {framework_slug!r} is not open (status is {framework['status']!r})")

    failure_count = 0

    for supplier_framework in data_api_client.find_framework_suppliers_iter(framework_slug):
        for user in data_api_client.find_users_iter(supplier_id=supplier_framework["supplierId"]):
            if user["active"]:
                # generating ref separately so we can exclude certain parameters from the personalization dict
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
                            {
                                "framework_name": framework["name"],
                                "updates_url":
                                    f"{get_web_url_from_stage(stage)}/suppliers/frameworks/{framework['slug']}/updates",
                                "clarification_questions_closed": (
                                    "no" if framework["clarificationQuestionsOpen"] else "yes"
                                ),
                            },
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
