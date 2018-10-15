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
    candidate_count, pass_count, fail_count, already_tagged_count = 0, 0, 0, 0

    def handle_version(version):
        # integer incrementing is "atomic" in python so it's ok to share these counters across threads. the reason we
        # don't pass the count back in the return value instead is that normal `map` implementations enforce the order
        # of yielded responses - as such a hanging request will impede progress of a (count summing) consumer, leaving
        # the counter lagging behind, which could result in an inaccurate count if aborted early.
        nonlocal candidate_count, pass_count, fail_count, already_tagged_count
        if since and version.get('LastModified') and version['LastModified'] < since:
            logger.debug("Ignoring file from %s: %s", version["LastModified"], version["Key"])
            return

        logger.info(
            f"{'(Would be) ' if dry_run else ''}Requesting scan of key %s version %s (%s)",
            version["Key"],
            version["VersionId"],
            version["LastModified"],
        )
        candidate_count += 1

        if not dry_run:
            result = antivirus_api_client.scan_and_tag_s3_object(
                bucket_name,
                version["Key"],
                version["VersionId"],
            )

            if result["avStatusApplied"]:
                if result.get("newAvStatus", {}).get("avStatus.result") == "pass":
                    pass_count += 1
                else:
                    fail_count += 1
                message = f"Marked with result {result.get('newAvStatus', {}).get('avStatus.result')}"
            else:
                already_tagged_count += 1
                message = f"Unchanged: "
                if result.get("existingAvStatus", {}).get("avStatus.result"):
                    message += f"already marked as {result['existingAvStatus']['avStatus.result']!r}"
                    if result.get("existingAvStatus", {}).get("avStatus.ts"):
                        message += f" ({result['existingAvStatus']['avStatus.ts']})"

            logger.info("%s: %s", version["VersionId"], message)

    try:
        for _ in map_callable(
            handle_version,
            chain.from_iterable(
                page.get("Versions") or ()
                for page in s3_client.get_paginator("list_object_versions").paginate(
                    Bucket=bucket_name,
                    Prefix=prefix,
                )
            ),
        ):
            # `map` produces a lazy iterable that has to be consumed for the action to be performed, but we don't care
            # about the result
            pass
    except BaseException as e:
        logger.warning(
            "Aborting with candidate_count = %s, pass_count = %s, fail_count = %s, already_tagged_count = %s",
            candidate_count,
            pass_count,
            fail_count,
            already_tagged_count,
        )
        raise

    return candidate_count, pass_count, fail_count, already_tagged_count
