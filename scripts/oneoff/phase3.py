import sys

from dmapiclient import DataAPIClient

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmutils.env_helpers import get_api_endpoint_from_stage

# Run this script from a directory containing phase3.csv - a list of the phase 3 suppliers.
with open("phase3.csv", 'r') as file:
    suppliers = [s.strip('\n') for s in file.readlines()]

stage = 'staging'
data_api_client = DataAPIClient(get_api_endpoint_from_stage(stage), get_auth_token('api', stage))

for supplier_id in suppliers:
    framework_info = data_api_client.get_supplier_framework_info(supplier_id, 'g-cloud-12')['frameworkInterest']

    if not framework_info['applicationCompanyDetailsConfirmed']:
        print(f"{supplier_id} - company details not confirmed")

    if framework_info['declaration']['status'] != "complete":
        print(f"{supplier_id} - declaration not complete")

    if not framework_info['onFramework']:
        print(f"{supplier_id} - company not on framework")

    if framework_info['agreementStatus'] != 'countersigned':
        print(f"{supplier_id} - company not countersigned: {framework_info['agreementStatus']}")
