from collections import Counter
import logging


import jsonschema


def _passes_validation(candidate, schema, logger, schema_name="schema", tablevel=0, loglevel=logging.INFO):
    try:
        jsonschema.validate(candidate, schema)
    except jsonschema.ValidationError as e:
        # extracting multiple errors from a single validation is possible but a bit more involved than i'm willing
        # to go right now
        logger.log(loglevel, "%sFailed %s @ %s: %s", "\t"*tablevel, schema_name, "/".join(e.absolute_path), e.message)
        return False
    else:
        return True


def _assess_draft_services(
        client,
        updated_by,
        framework_slug,
        supplier_id,
        service_schema=None,
        dry_run=True,
        reassess_failed_draft_services=False,
        logger=logging.getLogger("script"),
        ):
    counter = Counter()
    for draft_service in client.find_draft_services_iter(supplier_id, framework=framework_slug):
        if draft_service["status"] in ("submitted", "failed",):
            logger.debug("\tAssessing draft service %s", draft_service["id"])
            if draft_service["status"] == "failed" and not reassess_failed_draft_services:
                logger.debug("\t\tSkipping - already marked failed")
                counter["skipped"] += 1
            elif service_schema is None or _passes_validation(
                    draft_service,
                    service_schema,
                    logger,
                    schema_name="service_schema",
                    tablevel=2,
                    loglevel=logging.DEBUG,
                    ):
                if not dry_run:
                    # mark this as submitted
                    if draft_service["status"] != "submitted":
                        client.update_draft_service_status(draft_service["id"], "submitted", updated_by)
                    else:
                        logger.debug("\tUnchanged result - not re-setting")
                counter["passed"] += 1
            else:
                if not dry_run:
                    # mark this as failed
                    if draft_service["status"] != "failed":
                        client.update_draft_service_status(draft_service["id"], "failed", updated_by)
                    else:
                        logger.debug("\tUnchanged result - not re-setting")
                counter["failed"] += 1

    logger.info(
        "\tDraft services:  %s passed, %s failed, %s skipped",
        counter["passed"],
        counter["failed"],
        counter["skipped"],
    )
    return counter


def mark_definite_framework_results(
        client,
        updated_by,
        framework_slug,
        declaration_definite_pass_schema,
        declaration_baseline_schema=None,
        service_schema=None,
        dry_run=True,
        reassess_passed=False,
        reassess_failed=False,
        reassess_failed_draft_services=False,
        logger=logging.getLogger("script"),
        ):
    for supplier_id in client.get_interested_suppliers(framework_slug).get('interestedSuppliers', ()):
        logger.info("Supplier: %r", supplier_id)
        supplier_framework = client.get_supplier_framework_info(supplier_id, framework_slug)["frameworkInterest"]
        if (supplier_framework["onFramework"] is False and not reassess_failed) or \
                (supplier_framework["onFramework"] is True and not reassess_passed):
            logger.info("\tSkipping: already %s", "passed" if supplier_framework["onFramework"] else "failed")
            continue

        service_counter = _assess_draft_services(
            client,
            updated_by,
            framework_slug,
            supplier_id,
            service_schema=service_schema,
            dry_run=dry_run,
            reassess_failed_draft_services=reassess_failed_draft_services,
            logger=logger
        )

        if supplier_framework["declaration"].get("status") == "complete" and service_counter["passed"] and \
                _passes_validation(
                    supplier_framework["declaration"],
                    declaration_definite_pass_schema,
                    logger,
                    schema_name="declaration_definite_pass_schema",
                    tablevel=1,
                ):
            logger.info("\tResult: PASS")
            if not dry_run:
                if supplier_framework["onFramework"] is not True:
                    client.set_framework_result(supplier_id, framework_slug, True, updated_by)
                else:
                    logger.debug("\tUnchanged result - not re-setting")
        elif supplier_framework["declaration"].get("status") != "complete" or (not service_counter["passed"]) or \
                (declaration_baseline_schema and not _passes_validation(
                    supplier_framework["declaration"],
                    declaration_baseline_schema,
                    logger,
                    schema_name="declaration_baseline_schema",
                    tablevel=1,
                )):
            logger.info("\tResult: FAIL")
            if not dry_run:
                if supplier_framework["onFramework"] is not False:
                    client.set_framework_result(supplier_id, framework_slug, False, updated_by)
                else:
                    logger.debug("\tUnchanged result - not re-setting")
        else:
            # a result of DISCRETIONARY should pretty much never overwrite an already-made decision
            logger.info(
                "\tResult: DISCRETIONARY%s",
                " (but leaving as {})".format(
                    "PASS" if supplier_framework["onFramework"] else "FAIL"
                ) if supplier_framework["onFramework"] is not None else "",
            )
