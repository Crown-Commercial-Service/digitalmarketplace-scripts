from dmscripts.helpers.supplier_data_helpers import SupplierFrameworkDeclarations


def remove_supplier_data(data_api_client, logger, dry_run: bool, cutoff_date):
    supplier_frameworks = SupplierFrameworkDeclarations(
        api_client=data_api_client,
        logger=logger,
        dry_run=dry_run
    )
    supplier_frameworks.remove_supplier_declaration_for_expired_frameworks(cutoff_date)
