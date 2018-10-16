from itertools import chain
import logging


logger = logging.getLogger("script")


def virus_scan_bucket(
    s3_client,
    antivirus_api_client,
    bucket_name,
    prefix="",
    since=None,
    dry_run=True,
    map_callable=map,
):
    def handle_version(version):
        if since and version.get('LastModified') and version['LastModified'] < since:
            logger.debug("Ignoring file from %s: %s", version["LastModified"], version["Key"])
            return 0, 0, 0, 0

        candidate_count_inner, pass_count_inner, fail_count_inner, already_tagged_count_inner = 0, 0, 0, 0

        logger.info(
            f"{'(Would be) ' if dry_run else ''}Requesting scan of key %s version %s (%s)",
            version["Key"],
            version["VersionId"],
            version["LastModified"],
        )
        candidate_count_inner += 1

        if not dry_run:
            result = antivirus_api_client.scan_and_tag_s3_object(
                bucket_name,
                version["Key"],
                version["VersionId"],
            )

            if result["avStatusApplied"]:
                if result.get("newAvStatus", {}).get("avStatus.result") == "pass":
                    pass_count_inner += 1
                else:
                    fail_count_inner += 1
                message = f"Marked with result {result.get('newAvStatus', {}).get('avStatus.result')}"
            else:
                already_tagged_count_inner += 1
                message = f"Unchanged: "
                if result.get("existingAvStatus", {}).get("avStatus.result"):
                    message += f"already marked as {result['existingAvStatus']['avStatus.result']!r}"
                    if result.get("existingAvStatus", {}).get("avStatus.ts"):
                        message += f" ({result['existingAvStatus']['avStatus.ts']})"

            logger.info("%s: %s", version["VersionId"], message)

        return candidate_count_inner, pass_count_inner, fail_count_inner, already_tagged_count_inner

    total_candidate_count, total_pass_count, total_fail_count, total_already_tagged_count = 0, 0, 0, 0
    try:
        for candidate_count, pass_count, fail_count, already_tagged_count in map_callable(
            handle_version,
            chain.from_iterable(
                page.get("Versions") or ()
                for page in s3_client.get_paginator("list_object_versions").paginate(
                    Bucket=bucket_name,
                    Prefix=prefix,
                )
            ),
        ):
            total_candidate_count += candidate_count
            total_pass_count += pass_count
            total_fail_count += fail_count
            total_already_tagged_count += already_tagged_count
    except BaseException as e:
        logger.warning(
            "Aborting with candidate_count = %s, pass_count = %s, fail_count = %s, already_tagged_count = %s",
            total_candidate_count,
            total_pass_count,
            total_fail_count,
            total_already_tagged_count,
        )
        raise

    return total_candidate_count, total_pass_count, total_fail_count, total_already_tagged_count
