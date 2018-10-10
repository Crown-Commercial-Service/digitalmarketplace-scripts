from itertools import chain
import logging


logger = logging.getLogger("script")


def virus_scan_bucket(s3_client, antivirus_api_client, bucket_name, prefix="", since=None, dry_run=True):
    candidate_count, pass_count, fail_count, already_tagged_count = 0, 0, 0, 0

    for version in chain.from_iterable(
        page.get("Versions") or ()
        for page in s3_client.get_paginator("list_object_versions").paginate(
            Bucket=bucket_name,
            Prefix=prefix,
        )
    ):
        if since and version.get('LastModified') and version['LastModified'] < since:
            logger.debug("Ignoring file from %s: %s", version["LastModified"], version["Key"])
            continue

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

    return candidate_count, pass_count, fail_count, already_tagged_count
