from dmscripts.helpers.supplier_data_helpers import SupplierFrameworkDeclarations


def remove_supplier_data(data_api_client, logger, dry_run):
    supplier_frameworks = SupplierFrameworkDeclarations(
        api_client=data_api_client,
        logger=logger,
        dry_run=dry_run
    )
    supplier_frameworks.remove_supplier_declaration_for_expired_frameworks()


def remove_unsuccessful_supplier_declarations(data_api_client, logger, dry_run, framework_slug):
    supplier_frameworks_methods = SupplierFrameworkDeclarations(
        api_client=data_api_client,
        logger=logger,
        dry_run=dry_run
    )
    supplier_frameworks_methods.remove_declaration_from_failed_applicants(framework_slug)
