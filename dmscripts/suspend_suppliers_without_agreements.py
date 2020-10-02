from itertools import chain

from dmapiclient.audit import AuditTypes


def get_all_email_addresses_for_supplier(client, supplier_framework):
    # Combine the framework application contact email with all the active user emails
    return frozenset(chain(
        (supplier_framework["frameworkInterest"]["declaration"]["primaryContactEmail"],),
        (
            user["emailAddress"] for user in client.find_users_iter(
                supplier_id=int(supplier_framework['frameworkInterest']['supplierId'])
            ) if user["active"]
        ),
    ))


def suspend_supplier_services(client, logger, framework_slug, supplier_id, framework_info, dry_run):
    """
    The supplier ID list should have been flagged by CCS as requiring action, but double check that the supplier:
      - has some services on the framework
      - has `agreementReturned: false`
      - has not `agreementReturned: on-hold
    :param client: API client instance
    :param framework_info: JSON
    :param dry_run: don't suspend if True
    :return: suspended_service_count
    :rtype: int
    """
    suspended_service_count = 0

    # Ignore any 'private' services that the suppliers have removed themselves
    new_service_status, old_service_status = 'disabled', 'published'

    if not framework_info['frameworkInterest']['onFramework']:
        logger.error(f'Supplier {supplier_id} is not on the framework.')
        return suspended_service_count
    if framework_info['frameworkInterest']['agreementReturned']:
        logger.error(f'Supplier {supplier_id} has returned their framework agreement.')
        return suspended_service_count
    if framework_info['frameworkInterest']['agreementStatus'] == 'on-hold':
        logger.error(f"Supplier {supplier_id}'s framework agreement is on hold.")
        return suspended_service_count

    # Find the supplier's non-private services on this framework
    services = client.find_services(
        supplier_id=supplier_id, framework=framework_slug, status=old_service_status
    )
    if not services['services']:
        logger.error(f'Supplier {supplier_id} has no {old_service_status} services on the framework.')
        return suspended_service_count

    # Suspend all services for each supplier (the API will de-index the services from search results)
    logger.info(
        f"Setting {services['meta']['total']} services to '{new_service_status}' for supplier {supplier_id}."
    )
    for service in services['services']:
        if dry_run:
            logger.info(f"[DRY RUN] Would suspend service {service['id']} for supplier {supplier_id}")
        else:
            client.update_service_status(service['id'], new_service_status, "Suspend services script")
        suspended_service_count += 1

    # Return suspended service count (i.e. if > 0, some emails need to be sent)
    return suspended_service_count


def unsuspend_supplier_services(client, logger, framework_slug, supplier_id, framework_info, dry_run):
    """
    The supplier ID list should have been flagged by CCS as requiring action, but double check that the supplier:
      - has some services on the framework
      - has not `agreementReturned: false`
      - has not `agreementReturned: on-hold
    :param client: API client instance
    :param framework_info: JSON
    :param dry_run: don't suspend if True
    :return: suspended_service_count
    :rtype: int
    """
    unsuspended_service_count = 0

    new_service_status, old_service_status = 'published', 'disabled'

    if not framework_info['frameworkInterest']['onFramework']:
        logger.error(f'Supplier {supplier_id} is not on the framework.')
        return unsuspended_service_count
    if framework_info['frameworkInterest']['agreementReturned'] is None:
        logger.error(f'Supplier {supplier_id} has not returned their framework agreement.')
        return unsuspended_service_count
    if framework_info['frameworkInterest']['agreementStatus'] == 'on-hold':
        logger.error(f"Supplier {supplier_id}'s framework agreement is on hold.")
        return unsuspended_service_count

    # Find the supplier's services which were suspended by script
    suspended_services_on_framework = set(
        service["id"] for service in
        client.find_services(
            supplier_id=supplier_id, framework=framework_slug, status=old_service_status
        )["services"]
    )

    if not suspended_services_on_framework:
        logger.error(f'Supplier {supplier_id} has no {old_service_status} services on the framework.')
        return unsuspended_service_count

    services_suspended_by_script = set(
        event["data"]["serviceId"]
        for event in
        client.find_audit_events_iter(
            audit_type=AuditTypes.update_service_status,
            data_supplier_id=supplier_id,
            user="Suspend services script",
        )
    )

    service_ids = suspended_services_on_framework & services_suspended_by_script

    # Suspend all services for each supplier (the API will de-index the services from search results)
    logger.info(
        f"Setting {len(service_ids)} services to '{new_service_status}' for supplier {supplier_id}."
    )
    for service_id in service_ids:
        if dry_run:
            logger.info(f"[DRY RUN] Would suspend service {service_id} for supplier {supplier_id}")
        else:
            client.update_service_status(service_id, new_service_status, "Suspend services script")
        unsuspended_service_count += 1

    # Return suspended service count (i.e. if > 0, some emails need to be sent)
    return unsuspended_service_count
