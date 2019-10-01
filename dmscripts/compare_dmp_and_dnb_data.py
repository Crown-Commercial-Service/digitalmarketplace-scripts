import datetime
import numpy as np
import requests
import unicodecsv

from dmapiclient import DataAPIClient
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage


def levenshtein_ratio_and_distance(s, t, ratio_calc=False):
    """ levenshtein_ratio_and_distance:
        Calculates levenshtein distance between two strings.
        If ratio_calc = True, the function computes the
        levenshtein distance ratio of similarity between two strings
        For all i and j, distance[i,j] will contain the Levenshtein
        distance between the first i characters of s and the
        first j characters of t
    """
    # Initialize matrix of zeros
    rows = len(s) + 1
    cols = len(t) + 1
    distance = np.zeros((rows, cols), dtype=int)

    # Populate matrix of zeros with the indeces of each character of both strings
    for i in range(1, rows):
        for k in range(1, cols):
            distance[i][0] = i
            distance[0][k] = k

    # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row - 1] == t[col - 1]:
                cost = 0  # If the characters are the same in both strings in a given position [i,j] then the cost is 0
            else:
                # In order to align the results with those of the Python Levenshtein package,
                # if we choose to calculate the ratio the cost of a substitution is 2.
                # If we calculate just distance, then the cost of a substitution is 1.
                if ratio_calc is True:
                    cost = 2
                else:
                    cost = 1
            distance[row][col] = min(
                distance[row - 1][col] + 1,  # Cost of deletions
                distance[row][col - 1] + 1,  # Cost of insertions
                distance[row - 1][col - 1] + cost  # Cost of substitutions
            )
    if ratio_calc is True:
        # Computation of the Levenshtein Distance Ratio
        Ratio = ((len(s) + len(t)) - distance[row][col]) / (len(s) + len(t))
        return Ratio
    else:
        # print(distance) # Uncomment to see the matrix showing how the algorithm computes the cost of deletions,
        # insertions and/or substitutions
        # This is the minimum number of edits needed to convert string a to string b
        return f"The strings are {distance[row][col]} edits away"


class DNBAPIException(Exception):
    "Exception class for the D&B API errors, list here: https://docs.dnb.com/direct/2.0/en-US/response-codes"
    def __init__(self, code, text):
        self.code = code
        self.text = text


class DNBDirectAPIClient(object):
    "A client utilising the D&B direct API with methods used by the DMp API."

    def __init__(self, username, password, stage='production'):
        "initialisation with D&B credentials and optionally DMp stage"
        self.stage = stage
        self.data_api_client = None
        self.duns_number_compared = set()  # faster in operation than a list
        self.max_dnb_api_calls_per_method = 100
        self.root = 'https://direct.dnb.com'
        response = requests.post(
            f'{self.root}/Authentication/V2.0/',
            headers={
                'x-dnb-user': username,
                'x-dnb-pwd': password,
            }
        )
        self.dnb_auth_token = response.json()['AuthenticationDetail']['Token']

    def get_dnb_org_data(self, duns_number):
        "return a dictionary with all the information D&B has on the company with that DUNS number"
        response = requests.get(
            f'{self.root}/V6.0/organizations?match=true&MatchTypeText=Basic&DUNSNumber={str(duns_number)}',
            headers={
                'Authorization': self.dnb_auth_token,
            }
        )
        # CM000 is the response code the D&B API returns when a request has been completed successfully.
        # For more information on the D&B API response codes see the link at the DNBAPIException docstring.
        if response.json()['MatchResponse']['TransactionResult']['ResultID'] == 'CM000':
            return response.json()['MatchResponse']['MatchResponseDetail']['MatchCandidate'][0]
        else:
            raise DNBAPIException(
                response.json()['MatchResponse']['TransactionResult']['ResultID'],
                response.json()['MatchResponse']['TransactionResult']['ResultText']
            )

    def extract_dnb_org_data(self, dnb_data):
        "returns an array with the D&B data that can be compared with DMp's suppliers"
        return [
            # company name
            dnb_data.get('OrganizationPrimaryName', {}).get('OrganizationName', {}).get('$'),
            # UK company house number
            dnb_data.get('OrganizationIdentificationNumberDetail', {}).get('OrganizationIdentificationNumber'),
            # the 2 letter country code is in capital case of the primary address
            dnb_data.get('PrimaryAddress', {}).get('CountryISOAlpha2Code'),
            # primary postal code
            dnb_data.get('PrimaryAddress', {}).get('PostalCode'),
            # primary address
            next(iter(dnb_data.get('PrimaryAddress', {}).get('StreetAddressLine', {})), {}).get('LineText'),
        ]

    def get_dmp_supplier_data(self, framework=None, duns_number=None, from_declaration=False):
        "return the DMp data for a given DUNS number and initialises the DMp client if None"
        # TODO: error handling
        if self.data_api_client is None:
            self.data_api_client = DataAPIClient(
                base_url=get_api_endpoint_from_stage(self.stage), auth_token=get_auth_token('api', self.stage)
            )
        if duns_number is not None:
            return self.data_api_client.find_suppliers(duns_number=duns_number)
        elif framework is not None:
            # TODO: use iter instead -> digitalmarketplace-apiclient/blob/master/dmapiclient/data.py#L119
            # TODO: check pagination
            if from_declaration:
                return self.data_api_client.find_framework_suppliers(framework)
            return self.data_api_client.find_suppliers(framework=framework)
        # TODO: else raise error when duns or framework is None

    def extract_dmp_supplier_data(self, dmp_supplier_data, from_declaration=False):
        "returns an array with the DMp data that can be compared with D&B's organisations"
        if from_declaration:
            return [
                # company name
                dmp_supplier_data.get('declaration', {}).get('supplierRegisteredName'),
                # UK company house number
                dmp_supplier_data.get('declaration', {}).get('supplierCompanyRegistrationNumber'),
                # the 2 letter country code
                dmp_supplier_data.get('declaration', {}).get('supplierRegisteredCountry', '').replace('country:', ''),
                # 1st postcode
                dmp_supplier_data.get('declaration', {}).get('supplierRegisteredPostcode'),
                # 1st address
                dmp_supplier_data.get('declaration', {}).get('supplierRegisteredBuilding'),
            ]
        return [
            # company name
            dmp_supplier_data.get('registeredName'),
            # UK company house number
            dmp_supplier_data.get('companiesHouseNumber'),
            # the 2 letter country code
            dmp_supplier_data.get('registrationCountry', '').replace('country:', ''),
            # 1st postcode
            next(iter(dmp_supplier_data.get('contactInformation', []))).get('postcode'),
            # 1st address
            next(iter(dmp_supplier_data.get('contactInformation', []))).get('address1'),
        ]

    def compare_data(self, duns_number, dmp, dnb):
        """
        return a list of similarity ratios between the two APIs data
        [DUNS number, exists in D&B, Name, House Nr, Phone, Country, Postcode, Address, ]
        """
        if not dnb:
            return [duns_number, datetime.datetime.now(), ] + [0.] * 7
        return [
            duns_number,
            # timestamp
            datetime.datetime.now(),
            # does DUNS number exists in the D&B database
            1.,
            # fuzzy matching of the company's name
            0. if (
                dmp[0] is None or dnb[0] is None
            ) else levenshtein_ratio_and_distance(dmp[0].lower(), dnb[0].lower(), ratio_calc=True),
            # house nr exact match
            1. if dmp[1] is not None and dnb[1] is not None and dmp[1].lower() == dnb[1].lower() else 0.,
            # country exact match
            1. if dmp[2] != '' and dnb[2] is not None and dmp[2].lower() == dnb[2].lower() else 0.,
            # postcode fuzzy match
            0. if (
                dmp[3] is None or dnb[3] is None
            ) else levenshtein_ratio_and_distance(dmp[3].lower(), dnb[3].lower(), ratio_calc=True),
            # fuzzy matching of the company's address
            0. if (
                dmp[4] is None or dnb[4] is None
            ) else levenshtein_ratio_and_distance(dmp[4].lower(), dnb[4].lower(), ratio_calc=True),
            '',  # blank line for D&B API errors
        ]

    def fetch_and_compare_suppliers_data(self, duns_number):
        "compare one organisation/supplier's entry D&B with DMp data identified by its DUNS number"
        dmp_response = self.get_dmp_supplier_data(duns_number=duns_number)
        # TODO: if dmp_response.get('dunsNumber') is None: exit
        # TODO: if len(dmp_data['suppliers']) != 1 raise an error
        dmp = self.extract_dmp_supplier_data(dmp_response['suppliers'][0])
        try:
            dnb = self.extract_dnb_org_data(self.get_dnb_org_data(duns_number))
            return self.compare_data(duns_number, dmp, dnb)
        except DNBAPIException as e:
            return [
                dmp_response['suppliers'][0],
                datetime.datetime.now(),  # timestamp
                0.,  # is in D&B
                0.,  # company's name
                0.,  # company house
                0.,  # country exact match
                0.,  # postcode exact match
                0.,  # company's address
                f'{e.args[0]}: {e.args[1]}',  # D&B failure reason
            ]

    def compare_suppliers(self, dmp_supplier, from_declaration, export_dnb_data, export_dmp_data, counter, writer=None):
        duns_number = dmp_supplier.get(
            'declaration', {}
        ).get(
            'supplierDunsNumber'
        ) if from_declaration else dmp_supplier.get('dunsNumber')
        # don't compare if DMp has no DUNS for a supplier
        if duns_number is None:
            print(
                'NO DUNS NUMBER FOR', self.extract_dmp_supplier_data(
                    dmp_supplier, from_declaration=from_declaration
                )
            )  # TODO: raise/log error?
            return
        # excluding existing supplier of the CSV write or print the rest
        if duns_number not in self.duns_number_compared:
            dmp_data = self.extract_dmp_supplier_data(dmp_supplier, from_declaration=from_declaration)
            try:
                dnb_data = self.extract_dnb_org_data(self.get_dnb_org_data(duns_number))
                row = self.compare_data(
                    duns_number,
                    dmp_data,
                    dnb_data
                )
                if export_dnb_data:
                    row += dnb_data
                if export_dmp_data:
                    row += dmp_data
            except DNBAPIException as e:
                row = [
                    duns_number,
                    datetime.datetime.now(),  # timestamp
                    0.,  # is in D&B
                    0.,  # company's name
                    0.,  # company house
                    0.,  # country exact match
                    0.,  # postcode exact match
                    0.,  # company's address
                    f'{e.code}: {e.text}',  # D&B failure reason
                ]
                if export_dnb_data:
                    row += [None] * 5
                if export_dmp_data:
                    row += dmp_data
            if writer is not None:
                counter += 1
                print(duns_number)
                writer.writerow(row)  # TODO: extend with D&B data
                self.duns_number_compared.add(duns_number)  # add DUNS to set
                if counter >= self.max_dnb_api_calls_per_method:
                    return
            else:
                print(row)  # TODO: log maybe?

    def fetch_and_compare_frameworks_suppliers_data(
        self,
        frameworks=['g-cloud', 'digital-outcomes-and-specialists'],
        csv_filename=None,
        export_dnb_data=True,
        export_dmp_data=False,
        from_declaration=True
    ):
        "retrieve DMp suppliers of frameworks and call for each the D&B API to compare and optionally append to CSV"
        counter = 0
        # fetch all DUNS numbers from CSV and if it doesn't exist create it
        if csv_filename is not None:
            try:
                with open(csv_filename, 'rb') as f:
                    reader = unicodecsv.reader(f, encoding='utf-8')
                    next(reader)  # skip the CSV's header
                    for row in reader:
                        print(row)
                        self.duns_number_compared.add(row[0])
                    print(self.duns_number_compared)
            except FileNotFoundError:
                header = [
                    'DUNS number',
                    'Compared at',
                    'In D&B?',
                    'Name',
                    'Company House',
                    'Country',
                    'Postcode',
                    'Address',
                    'D&B Error',
                ]
                if export_dnb_data:
                    header += [
                        'D&B Name',
                        'D&B Company House',
                        'D&B Country',
                        'D&B Postcode',
                        'D&B Address',
                    ]
                if export_dmp_data:
                    header += [
                        'DMp Name',
                        'DMp Company House',
                        'DMp Country',
                        'DMp Postcode',
                        'DMp Address',
                    ]
                with open(csv_filename, 'wb') as f:
                    writer = unicodecsv.writer(f, encoding='utf-8')
                    writer.writerow(header)
            # open for write later
            f = open(csv_filename, 'ab')  # file handle is closed at the end of the method
            writer = unicodecsv.writer(f, encoding='utf-8')
        # iterate all the suppliers of the frameworks
        for framework in frameworks:
            dmp_response = self.get_dmp_supplier_data(framework=framework, from_declaration=from_declaration)
            if from_declaration:
                dmp_response = dmp_response.get('supplierFrameworks', [])
            else:
                dmp_response = dmp_response.get('suppliers', [])
            for dmp_supplier in dmp_response:
                self.compare_suppliers(
                    dmp_supplier, from_declaration, export_dnb_data, export_dmp_data, counter, writer
                )
        # close file resource if necessary
        if csv_filename is not None:
            f.close()
