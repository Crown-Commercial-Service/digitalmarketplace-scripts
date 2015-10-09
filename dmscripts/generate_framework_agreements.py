# -*- coding: utf-8 -*-
import unicodecsv


class Supplier:

    def __init__(self, declaration, lots):
        self.bidder_name = declaration[1]
        self.registered_company_name = declaration[1]
        self.country_of_registration = declaration[1]
        self.company_number = declaration[1]
        self.registered_office_address = declaration[1]
        self.contact_name = declaration[1]
        self.contact_email = declaration[1]


def read_csv(filepath):
    csv_file = unicodecsv.reader(filepath, delimiter=',', quotechar='"')
    return []


def build_supplier(lots, declarations):
    supplier = {
        "declarations": {},
        "lots": {}
    }

    for declaration in declarations:
        supplier['declarations'][declaration[0]] = declaration

    for lot in lots:
        supplier['lots'][lot[0]] = lot


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
        print("row len={}".format(len(row)))
        if len(row) != columns:
            return False, "Row incorrect length"

        for field in required_fields:
            if not row[field]:
                return False, "Row missing required field {}".format(row)

    return True


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
    columns = 58
    required_fields = [0, 1, 2]  # these are identifiers, not checked the actual fields here

    for index, row in enumerate(declaration_file):
        print("row len={}".format(len(row)))
        if len(row) != columns:
            return False, "Row incorrect length row: {}".format(index)

        for field in required_fields:
            if not row[field]:
                return False, "Row missing required field row: {} field: {}".format(index, field)

    return True

if __name__ == "__main__":
    import doctest
    doctest.testmod()
