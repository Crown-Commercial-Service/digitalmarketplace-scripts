# -*- coding: utf-8 -*-
import os
import unicodecsv

from fdfgen import forge_fdf
from subprocess import call


class Supplier:

    def __init__(self, declaration, lots):
        if declaration[0] != lots[0]:
            raise Exception("Supplier ID for lots does not match declaration")

        self.supplier_id = declaration[0]

        self.bidder_name = declaration[24]
        self.registered_company_name = declaration[20]
        self.country_of_registration = declaration[26]
        self.company_number = declaration[27]
        self.registered_office_address = declaration[21]
        self.contact_name = declaration[18]
        self.contact_email = declaration[19]

        self.lot1 = "IaaS" if int(lots[3]) > 0 else ""
        self.lot2 = "SaaS" if int(lots[7]) > 0 else ""
        self.lot3 = "PaaS" if int(lots[5]) > 0 else ""
        self.lot4 = "SCS" if int(lots[9]) > 0 else ""

    def __str__(self):
        return "ID: {}, BidderName:{}, RegName:{}, Country:{}, Num:{}, Addr:{}, Name:{}, email:{}".format(
            self.supplier_id, self.bidder_name, self.registered_company_name, self.country_of_registration,
            self.company_number, self.registered_office_address, self.contact_name, self.contact_email)


def read_csv(filepath):
    all_rows = []
    with open(filepath, 'r') as csvfile:
        csv_file = unicodecsv.reader(csvfile, delimiter=',', quotechar='"')
        for row in csv_file:
            all_rows.append(row)
    return all_rows


def build_framework_agreements(declarations, lots, output_dir, framework_form):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for declaration in declarations:
        supplier_id = declaration[0]
        lot = lot_for_supplier_id(lots, supplier_id)
        if lot:
            _generate_framework_fdf(declaration, lot, output_dir)
            _generate_framework_pdf(supplier_id, output_dir, framework_form)


def _generate_framework_fdf(declaration, lot, output_dir):
    supplier = Supplier(declaration, lot)
    print("SUPPLIER: {}".format(supplier))
    fields = [
        ('Bidder Name', supplier.bidder_name),
        ('Registered Company Name', supplier.registered_company_name),
        ('Country of Registration', supplier.country_of_registration),
        ('Registered Company Number', supplier.company_number),
        ('Registered Address', supplier.registered_office_address),
        ('Framework Contact Name', supplier.contact_name),
        ('Framework Contact Email address', supplier.contact_email),
        ('Lot1', supplier.lot1),
        ('Lot2', supplier.lot2),
        ('Lot3', supplier.lot3),
        ('Lot4', supplier.lot4)
    ]
    print("FIELDS: {}".format(fields))
    fdf = forge_fdf("", fields, [], [], [])
    fdf_filename = "{}/{}-framework-data.fdf".format(output_dir, supplier.supplier_id)
    fdf_file = open(fdf_filename, "wb")
    fdf_file.write(fdf)
    fdf_file.close()


def _generate_framework_pdf(supplier_id, output_dir, framework_form):
    fdf_filename = "{}/{}-framework-data.fdf".format(output_dir, supplier_id)
    print("FDF FILE: {}".format(fdf_filename))
    if os.path.isfile(fdf_filename):
        pdf_filename = "{}/{}-g7-framework-agreement.pdf".format(output_dir, supplier_id)
        call(["pdftk", framework_form, "fill_form", fdf_filename, "output", pdf_filename])
    else:
        raise Exception("FDF file does not exist: {}".format(fdf_filename))


def lot_for_supplier_id(lots, supplier_id):
    for lot in lots:
        if lot[0] == supplier_id:
            return lot
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
    required_fields = [0, 1, 2]

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
    required_fields = [0, 1, 2]  # these are identifiers, not checked the actual fields here

    for index, row in enumerate(declaration_file):
        print("ROW LEN: {}".format(len(row)))
        if len(row) != columns:
            return False, "Row incorrect length row: {}".format(index)

        for field in required_fields:
            if not row[field]:
                return False, "Row missing required field row: {} field: {}".format(index, field)
    return True, "Declarations file OK"

if __name__ == "__main__":
    import doctest
    doctest.testmod()
