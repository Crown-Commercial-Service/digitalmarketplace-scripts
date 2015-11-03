# -*- coding: utf-8 -*-
import os
from dmutils.apiclient.errors import HTTPError
from dmutils.documents import sanitise_supplier_name

import sys
if sys.version_info > (3, 0):
    import csv
else:
    import unicodecsv as csv


class Supplier:

    def __init__(self, declaration, lots):
        if declaration[0] != lots[0]:
            raise Exception("Supplier ID for lots does not match declaration")

        self.supplier_id = declaration[0]

        self.registered_company_name = declaration[20]
        self.country_of_registration = declaration[26]
        self.company_number = declaration[27]
        self.registered_office_address = declaration[21]
        self.contact_name = declaration[18]
        self.contact_email = declaration[19]

        self.lot1 = "Lot 1: Infrastructure as a Service (IaaS)" if int(lots[3]) > 0 else ""
        self.lot2 = "Lot 2: Platform as a Service (PaaS)" if int(lots[5]) > 0 else ""
        self.lot3 = "Lot 3: Software as a Service (SaaS)" if int(lots[7]) > 0 else ""
        self.lot4 = "Lot 4: Specialist Cloud Services (SCS)" if int(lots[9]) > 0 else ""

    def __str__(self):
        return "ID: {}, RegName:{}, Country:{}, Num:{}, Addr:{}, Name:{}, email:{}".format(
            self.supplier_id, self.registered_company_name, self.country_of_registration,
            self.company_number, self.registered_office_address, self.contact_name, self.contact_email)


class FailedSupplier:

    def __init__(self, declaration):
        self.supplier_id = declaration[0]
        self.registered_company_name = declaration[20]


def read_csv(filepath):
    all_rows = []
    with open(filepath, 'r') as csvfile:
        csv_file = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in csv_file:
            all_rows.append(row)
    return all_rows


def make_filename_key(supplier_name, supplier_id):
    return "{}-{}".format(sanitise_supplier_name(supplier_name), supplier_id)


def supplier_is_on_framework(client, supplier_id):
    try:
        framework_interest = client.get_supplier_framework_info(supplier_id, 'g-cloud-7')
        return framework_interest['frameworkInterest']['onFramework']
    except HTTPError as e:
        print("ERROR checking if supplier {} is on framework: {}".format(supplier_id, str(e)))
        return False


def build_framework_agreements(client, declarations, lots, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open('{}/g7-framework-data.tsv'.format(output_dir), 'w') as csvfile:
        with open('{}/g7-fail-data.tsv'.format(output_dir), 'w') as failfile:
            # This defines the order of the fields - fields can be in any order in
            # the dictionary for each row and will be mapped to the order defined here.
            fieldnames = [
                'Key',
                'Supplier ID',
                'Registered Company Name',
                'Country of Registration',
                'Registered Company Number',
                'Registered Address',
                'Framework Contact Name',
                'Framework Contact Email address',
                'Lot1',
                'Lot2',
                'Lot3',
                'Lot4',
                'Lot1Letter',
                'Lot2Letter',
                'Lot3Letter',
                'Lot4Letter',
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect='excel-tab')
            writer.writeheader()

            fail_fieldnames = [
                'Key',
                'Supplier ID',
                'Registered Company Name'
            ]
            fail_writer = csv.DictWriter(failfile, fieldnames=fail_fieldnames, dialect='excel-tab')
            fail_writer.writeheader()

            for declaration in declarations:
                supplier_id = declaration[0]
                on_framework = supplier_is_on_framework(client, supplier_id)
                if on_framework is True:
                    lot_count = lot_counts_for_supplier_id(lots, supplier_id)
                    if lot_count:
                        supplier = Supplier(declaration, lot_count)
                        row = {
                            'Key': make_filename_key(supplier.registered_company_name, supplier.supplier_id),
                            'Supplier ID': supplier.supplier_id,
                            'Registered Company Name': supplier.registered_company_name,
                            'Country of Registration': supplier.country_of_registration,
                            'Registered Company Number': supplier.company_number,
                            'Registered Address': supplier.registered_office_address,
                            'Framework Contact Name': supplier.contact_name,
                            'Framework Contact Email address': supplier.contact_email,
                            'Lot1': supplier.lot1,
                            'Lot2': supplier.lot2,
                            'Lot3': supplier.lot3,
                            'Lot4': supplier.lot4,
                            'Lot1Letter': "Pass" if supplier.lot1 else "No bid",
                            'Lot2Letter': "Pass" if supplier.lot2 else "No bid",
                            'Lot3Letter': "Pass" if supplier.lot3 else "No bid",
                            'Lot4Letter': "Pass" if supplier.lot4 else "No bid",
                        }
                        writer.writerow(row)
                elif on_framework is False:
                    print("Failed supplier: {}".format(supplier_id))
                    supplier = FailedSupplier(declaration)
                    row = {
                        'Key': make_filename_key(supplier.registered_company_name, supplier.supplier_id),
                        'Supplier ID': supplier.supplier_id,
                        'Registered Company Name': supplier.registered_company_name,
                    }
                    fail_writer.writerow(row)
                else:
                    print("Supplier did not apply: {}".format(supplier_id))
                    continue


def lot_counts_for_supplier_id(lot_counts, supplier_id):
    for lot_count in lot_counts:
        if lot_count[0] == supplier_id:
            return lot_count
    print("No lot counts for supplier: {}".format(supplier_id))
    return None


def check_lots_csv(lots_file):
    """ Check a supplier lots file has right number of columns and all the required fields
    >>> f = read_csv("test_files/example-lots.csv")
    >>> print f
    >>> check_lots_csv(f)
    True
    >>> f = [[],[93584,"Akamai Technologies Ltd",123456789,1,2,0,3,0,1,2,1]]
    >>> check_lots_csv(f)
    (False, 'Row incorrect length')
    >>> f = [[93584,"Akamai Technologies Ltd","",1,2,0,3,0,1,2,1]]
    >>> check_lots_csv(f)
    (False, "Row missing required field [93584, 'Akamai Technologies Ltd', '', 1, 2, 0, 3, 0, 1, 2, 1]")
    """
    columns = 11
    required_fields = [0, 3, 5, 7, 9]

    for row in lots_file:
        if len(row) != columns:
            return False, "Row incorrect length"

        for field in required_fields:
            if not row[field]:
                return False, "Row missing required field {}".format(row)

    return True, "Lots file OK"


def check_declarations_csv(declaration_file):
    """ Check a supplier declaraion file has right number of columns and all the required fields
    >>> f = [[92191, "Accenture (UK) Limited", 734939007, "yes", "yes", "yes", "yes", "yes", "yes", "failed", "yes", "yes", "yes", "yes", "yes", "Yes – your organisation has or will have in place, employer's liability insurance of at least £5 million and you will provide certification prior to framework award.", "failed", "a", "ashraf.chohan@digital.cabinet-office.gov.uk", "a", "a", "public limited company", "a", "a", "1976", "uk", "a", "123456789", "yes", "yes", "a", "licensed", "a", "micro", "yourself without the use of third parties (subcontractors)", "a", "ashraf.chohan@digital.cabinet-office.gov.uk", "no", "no", "no", "yes", "no", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "a", "yes", "yes", "a"]]  # noqa
    >>> check_declarations_file(f)
    True
    >>> f = [[], [92191, "Accenture (UK) Limited", 734939007, "yes", "yes", "yes", "yes", "yes", "yes", "failed", "yes", "yes", "yes", "yes", "yes", "Yes – your organisation has or will have in place, employer's liability insurance of at least £5 million and you will provide certification prior to framework award.", "failed", "a", "ashraf.chohan@digital.cabinet-office.gov.uk", "a", "a", "public limited company", "a", "a", "1976", "uk", "a", "123456789", "yes", "yes", "a", "licensed", "a", "micro", "yourself without the use of third parties (subcontractors)", "a", "ashraf.chohan@digital.cabinet-office.gov.uk", "no", "no", "no", "yes", "no", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "a", "yes", "yes", "a"]]  # noqa
    >>> check_declarations_file(f)
    (False, 'Row incorrect length row: 0')
    >>> f = [[92191, "Accenture (UK) Limited", "", "yes", "yes", "yes", "yes", "yes", "yes", "failed", "yes", "yes", "yes", "yes", "yes", "Yes – your organisation has or will have in place, employer's liability insurance of at least £5 million and you will provide certification prior to framework award.", "failed", "a", "ashraf.chohan@digital.cabinet-office.gov.uk", "a", "a", "public limited company", "a", "a", "1976", "uk", "a", "123456789", "yes", "yes", "a", "licensed", "a", "micro", "yourself without the use of third parties (subcontractors)", "a", "ashraf.chohan@digital.cabinet-office.gov.uk", "no", "no", "no", "yes", "no", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "yes", "a", "yes", "yes", "a"]]  # noqa
    >>> check_declarations_file(f)
    (False, 'Row missing required field row: 0 field: 2')
    """
    columns = 59
    required_fields = [0, 18, 19, 20, 21, 26, 27]

    for index, row in enumerate(declaration_file):
        if len(row) != columns:
            return False, "Row incorrect length row: {}".format(index)

        if row[3] == 'complete':
            for field in required_fields:
                if not row[field]:
                    return False, "Row missing required field row: {} field: {}".format(index, field)
    return True, "Declarations file OK"

if __name__ == "__main__":
    import doctest
    doctest.testmod()
