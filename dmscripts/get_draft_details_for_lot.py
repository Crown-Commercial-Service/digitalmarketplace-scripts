import sys
from generate_user_email_list_applications import find_suppliers, get_all_supplier_framework_info

if sys.version_info > (3, 0):
    import csv
else:
    import unicodecsv as csv


def find_all_drafts(data_api_client, supplier_frameworks, framework_slug, lot_slug):
    drafts = []
    for supplier_framework in supplier_frameworks:
        supplier_drafts = data_api_client.find_draft_services_iter(supplier_id = supplier_framework['supplierId'],
                                                                   framework=framework_slug)
        for draft in supplier_drafts:
            if draft['lot'] == lot_slug:
                drafts.append(draft)
    return drafts


def get_anonymised_services(data_api_client, framework_slug, lot_slug):
    suppliers = find_suppliers(data_api_client)
    supplier_frameworks = get_all_supplier_framework_info(data_api_client, framework_slug, suppliers)
    drafts = find_all_drafts(data_api_client, supplier_frameworks, framework_slug, lot_slug)

    with open('{}-{}-draft-data.csv'.format(framework_slug, lot_slug), 'w') as csvfile:
        # This defines the order of the fields - fields can be in any order in
        # the dictionary for each row and will be mapped to the order defined here.
        fieldnames = [
            'Supplier',
            'Status',
            'agileCoachPriceMin',
            'agileCoachPriceMax',
            'agileCoachLocations',
            'businessAnalystPriceMin',
            'businessAnalystPriceMax',
            'businessAnalystLocations',
            'communicationsManagerPriceMin',
            'communicationsManagerPriceMax',
            'communicationsManagerLocations',
            'contentDesignerPriceMin',
            'contentDesignerPriceMax',
            'contentDesignerLocations',
            'securityConsultantPriceMin',
            'securityConsultantPriceMax',
            'securityConsultantLocations',
            'deliveryManagerPriceMin',
            'deliveryManagerPriceMax',
            'deliveryManagerLocations',
            'designerPriceMin',
            'designerPriceMax',
            'designerLocations',
            'developerPriceMin',
            'developerPriceMax',
            'developerLocations',
            'performanceAnalystPriceMin',
            'performanceAnalystPriceMax',
            'performanceAnalystLocations',
            'portfolioManagerPriceMin',
            'portfolioManagerPriceMax',
            'portfolioManagerLocations',
            'productManagerPriceMin',
            'productManagerPriceMax',
            'productManagerLocations',
            'programmeManagerPriceMin',
            'programmeManagerPriceMax',
            'programmeManagerLocations',
            'qualityAssurancePriceMin',
            'qualityAssurancePriceMax',
            'qualityAssuranceLocations',
            'serviceManagerPriceMin',
            'serviceManagerPriceMax',
            'serviceManagerLocations',
            'technicalArchitectPriceMin',
            'technicalArchitectPriceMax',
            'technicalArchitectLocations',
            'userResearcherPriceMin',
            'userResearcherPriceMax',
            'userResearcherLocations',
            'webOperationsPriceMin',
            'webOperationsPriceMax',
            'webOperationsLocations',
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
        writer.writeheader()

        id_counter = 1
        id_mappings = {}
        for draft in drafts:
            if draft['supplierId'] in id_mappings:
                id = id_mappings[draft['supplierId']]
            else:
                id = id_counter
                id_mappings[draft['supplierId']] = id_counter
                id_counter += 1
            row = {
                'Supplier': id,
                'Status': draft.get('status'),
                'agileCoachPriceMin': draft.get('agileCoachPriceMin', None),
                'agileCoachPriceMax': draft.get('agileCoachPriceMax', None),
                'agileCoachLocations': '-'.join(draft.get('agileCoachLocations', [])),
                'businessAnalystPriceMin': draft.get('businessAnalystPriceMin', None),
                'businessAnalystPriceMax': draft.get('businessAnalystPriceMax', None),
                'businessAnalystLocations': '-'.join(draft.get('businessAnalystLocations', [])),
                'communicationsManagerPriceMin': draft.get('communicationsManagerPriceMin', None),
                'communicationsManagerPriceMax': draft.get('communicationsManagerPriceMax', None),
                'communicationsManagerLocations': '-'.join(draft.get('communicationsManagerLocations', [])),
                'contentDesignerPriceMin': draft.get('contentDesignerPriceMin', None),
                'contentDesignerPriceMax': draft.get('contentDesignerPriceMax', None),
                'contentDesignerLocations': '-'.join(draft.get('contentDesignerLocations', [])),
                'securityConsultantPriceMin': draft.get('securityConsultantPriceMin', None),
                'securityConsultantPriceMax': draft.get('securityConsultantPriceMax', None),
                'securityConsultantLocations': '-'.join(draft.get('securityConsultantLocations', [])),
                'deliveryManagerPriceMin': draft.get('deliveryManagerPriceMin', None),
                'deliveryManagerPriceMax': draft.get('deliveryManagerPriceMax', None),
                'deliveryManagerLocations': '-'.join(draft.get('deliveryManagerLocations', [])),
                'designerPriceMin': draft.get('designerPriceMin', None),
                'designerPriceMax': draft.get('designerPriceMax', None),
                'designerLocations': '-'.join(draft.get('designerLocations', [])),
                'developerPriceMin': draft.get('developerPriceMin', None),
                'developerPriceMax': draft.get('developerPriceMax', None),
                'developerLocations': '-'.join(draft.get('developerLocations', [])),
                'performanceAnalystPriceMin': draft.get('performanceAnalystPriceMin', None),
                'performanceAnalystPriceMax': draft.get('performanceAnalystPriceMax', None),
                'performanceAnalystLocations': '-'.join(draft.get('performanceAnalystLocations', [])),
                'portfolioManagerPriceMin': draft.get('portfolioManagerPriceMin', None),
                'portfolioManagerPriceMax': draft.get('portfolioManagerPriceMax', None),
                'portfolioManagerLocations': '-'.join(draft.get('portfolioManagerLocations', [])),
                'productManagerPriceMin': draft.get('productManagerPriceMin', None),
                'productManagerPriceMax': draft.get('productManagerPriceMax', None),
                'productManagerLocations': '-'.join(draft.get('productManagerLocations', [])),
                'programmeManagerPriceMin': draft.get('programmeManagerPriceMin', None),
                'programmeManagerPriceMax': draft.get('programmeManagerPriceMax', None),
                'programmeManagerLocations': '-'.join(draft.get('programmeManagerLocations', [])),
                'qualityAssurancePriceMin': draft.get('qualityAssurancePriceMin', None),
                'qualityAssurancePriceMax': draft.get('qualityAssurancePriceMax', None),
                'qualityAssuranceLocations': '-'.join(draft.get('qualityAssuranceLocations', [])),
                'serviceManagerPriceMin': draft.get('serviceManagerPriceMin', None),
                'serviceManagerPriceMax': draft.get('serviceManagerPriceMax', None),
                'serviceManagerLocations': '-'.join(draft.get('serviceManagerLocations', [])),
                'technicalArchitectPriceMin': draft.get('technicalArchitectPriceMin', None),
                'technicalArchitectPriceMax': draft.get('technicalArchitectPriceMax', None),
                'technicalArchitectLocations': '-'.join(draft.get('technicalArchitectLocations', [])),
                'userResearcherPriceMin': draft.get('userResearcherPriceMin', None),
                'userResearcherPriceMax': draft.get('userResearcherPriceMax', None),
                'userResearcherLocations': '-'.join(draft.get('userResearcherLocations', [])),
                'webOperationsPriceMin': draft.get('webOperationsPriceMin', None),
                'webOperationsPriceMax': draft.get('webOperationsPriceMax', None),
                'webOperationsLocations': '-'.join(draft.get('webOperationsLocations', [])),
            }
            writer.writerow(row)
