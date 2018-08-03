#!/usr/bin/env python
# coding=utf-8

"""
Script to generate, submit, approve and index fake services from the validation JSON schemas
Only tested to work against g-cloud-9

Pre-requisites:
1) JSON Validation Schemas (as generated in dm-frameworks) for any lots you wish to use
  a) Filepath: dm-scripts/schemas/service-<framework_slug>-<lot_name>.json
2) JSON Validation Schema for the supplier declaration
  b) Filepath: dm-scrits/schemas/<framework_slug>.declaration.json

What this script does (semantically):
0) Store the current framework state so that it can be restored at the end.
1) Set a given (new) framework to open
2) Find some suppliers with services on a given (old) framework (e.g. g-cloud-7)
    a) For each supplier, register interest in a given (new) framework
    b) Submit and mark as complete a valid supplier declaration for the new framework
3) Submit draft services through randomly selected suppliers.
4) Set a given (new) framework to standstill
    a) Runs the `mark-definite-framework-results.py` script to mark x suppliers as on the new framework.
    b) Runs the `make-dos-live.py` script
5) Set a given (new) framework to live
6) Runs the `index-to-search-service.py` script to index the new services
7) Return the framework to its initial state.


usage: generate-fake-g-cloud-services.py [-h] [--new-slug NEW_SLUG]
                                         [--old-slug OLD_SLUG] [--env ENV]
                                         [--data-api-token DATA_API_TOKEN]
                                         [--search-api-token SEARCH_API_TOKEN]
                                         [--validation-schema-path VALIDATION_SCHEMA_PATH]
                                         [--supplier-count SUPPLIER_COUNT]
                                         [--lots LOTS]
                                         quantity

positional arguments:
  quantity              How many services to generate

optional arguments:
  -h, --help            show this help message and exit
  --new-slug NEW_SLUG, --new NEW_SLUG, -n NEW_SLUG
                        The (new) g-cloud framework slug to generate services
                        against (default=g-cloud-9)
  --old-slug OLD_SLUG, --old OLD_SLUG, -o OLD_SLUG
                        The (old) g-cloud framework to use to find suppliers
                        for new services (default=g-cloud-7)
  --env ENV, --stage ENV, -e ENV
                        Which environment to target for service ingestion
                        (default=local)
  --data-api-token DATA_API_TOKEN, -d DATA_API_TOKEN
                        The data API token for the selected stage
                        (default=myToken)
  --search-api-token SEARCH_API_TOKEN, -s SEARCH_API_TOKEN
                        The search API token for the selected stage
                        (default=myToken)
  --validation-schema-path VALIDATION_SCHEMA_PATH, -a VALIDATION_SCHEMA_PATH
                        The (relative or absolute) path to service validation
                        schemas (default='../digitalmarketplace-
                        api/json_schemas/'
  --supplier-count SUPPLIER_COUNT, -c SUPPLIER_COUNT
                        The number of suppliers to select for submitting new
                        services (default=100)
  --lots LOTS           Comma-separated list of lots to generate services for
                        (default=cloud-hosting,cloud-software,cloud-support)

"""

import argparse
import getpass
import random
import subprocess
import sys
sys.path.insert(0, '.')

from datetime import date

from dmapiclient import DataAPIClient, SearchAPIClient
from dmscripts.json_schema_service_faker import JsonSchemaGCloudServiceFaker
from dmscripts.helpers.service_faker_helpers import eligible_g9_declaration_base, gen_gcloud_name
from dmutils.env_helpers import get_api_endpoint_from_stage

LOTS_WHITELIST = ['cloud-hosting', 'cloud-software', 'cloud-support']
G9_LOTS = LOTS_WHITELIST
SUPPLIER_BLACKLIST = [11111, 11112]


def get_args():
    a = argparse.ArgumentParser()

    a.add_argument('--new-slug', '--new', '-n', type=str, default='g-cloud-9',
                   help="The (new) g-cloud framework slug to generate services against (default=g-cloud-9)")

    a.add_argument('--old-slug', '--old', '-o', type=str, default='g-cloud-7',
                   help="The (old) g-cloud framework to use to find suppliers for new services (default=g-cloud-7)")

    a.add_argument('--env', '--stage', '-e', type=str, default='local',
                   help="Which environment to target for service ingestion (default=local)")

    a.add_argument('--data-api-token', '-d', type=str, default='myToken',
                   help="The data API token for the selected stage (default=myToken)")

    a.add_argument('--search-api-token', '-s', type=str, default='myToken',
                   help="The search API token for the selected stage (default=myToken)")

    a.add_argument('--validation-schema-path', '-a', type=str, default='../digitalmarketplace-api/json_schemas/',
                   help="The (relative or absolute) path to service validation schemas "
                        "(default='../digitalmarketplace-api/json_schemas/'")

    a.add_argument('--supplier-count', '-c', type=int, default=100,
                   help="The number of suppliers to select for submitting new services (default=100)")

    a.add_argument('--lots', type=str, default=','.join(G9_LOTS),
                   help="Comma-separated list of lots to generate services for (default={})".format(','.join(G9_LOTS)))

    a.add_argument('quantity', type=int,
                   help="How many services to generate")

    return a.parse_args()


def filepath_service_lot_schema(validation_schema_path, new_slug, chosen_lot):
    return '{}/services-{}-{}.json'.format(validation_schema_path, new_slug, chosen_lot)


if __name__ == '__main__':
    args = get_args()

    args.env = args.env.lower()
    if args.env not in ['dev', 'development', 'local', 'preview', 'staging']:
        print("This script can only be run against dev/preview/staging environments.")
        sys.exit(1)

    args.lots = args.lots.lower().split(',')
    if set(args.lots) - set(LOTS_WHITELIST):
        print("This script only allows the following lots: {}. If you need other lots, please add them to the "
              "whitelist (this is just a sanity-check against typos).".format(LOTS_WHITELIST))
        sys.exit(1)

    data_api_url = get_api_endpoint_from_stage(args.env, 'api')
    data_api_client = DataAPIClient(data_api_url, args.data_api_token)

    search_api_url = get_api_endpoint_from_stage(args.env, 'search-api')
    search_api_client = SearchAPIClient(search_api_url, args.search_api_token)

    services_generated = 0
    gcloud_service_faker = JsonSchemaGCloudServiceFaker()
    email_address = "script@digitalmarketplace.service.gov.uk"
    identity = 'generate-g-cloud-services script ({})'.format(getpass.getuser())
    filepath_declaration_validator = 'schemas/{}.declaration.json'.format(args.new_slug)

    # 0) Store the current framework state so that it can be restored at the end.
    current_framework_state = data_api_client.get_framework(args.new_slug)['frameworks']['status']

    # 1) Set a given (new) framework to open
    data_api_client._post_with_updated_by(url='{}/frameworks/{}'.format(data_api_url, args.new_slug),
                                          data={"frameworks": {"status": "open"}},
                                          user=identity)

    # 2) Find some suppliers with services on a given (old) framework (e.g. g-cloud-7)
    suppliers = data_api_client.find_framework_suppliers(framework_slug=args.old_slug)['supplierFrameworks']
    suppliers = [x for x in suppliers if x['supplierId'] not in SUPPLIER_BLACKLIST]
    suppliers = random.sample(suppliers, args.supplier_count)
    suppliers_prepared = set()

    # 3) Submit draft services through randomly selected suppliers.
    while services_generated < args.quantity:
        random_lot = random.choice(args.lots)
        random_supplier = random.choice(suppliers)

        supplier_id = random_supplier['supplierId']
        if supplier_id not in suppliers_prepared:
            # 2a) For each supplier, register interest in a given (new) framework
            data_api_client.register_framework_interest(supplier_id=supplier_id,
                                                        framework_slug=args.new_slug,
                                                        user=identity)

            # 2b) Submit and mark as complete a valid supplier declaration for the new framework
            data_api_client.set_supplier_declaration(supplier_id=supplier_id,
                                                     framework_slug=args.new_slug,
                                                     declaration=eligible_g9_declaration_base(),
                                                     user=identity)

            suppliers_prepared.add(supplier_id)

        fake_service = gcloud_service_faker.generate_from_file(filepath_service_lot_schema(args.validation_schema_path,
                                                                                           args.new_slug, random_lot))
        fake_service['serviceName'] = gen_gcloud_name()

        draft_service = data_api_client.create_new_draft_service(framework_slug=args.new_slug,
                                                                 lot=random_lot,
                                                                 supplier_id=supplier_id,
                                                                 data=fake_service,
                                                                 user=identity)

        data_api_client.complete_draft_service(draft_id=draft_service['services']['id'],
                                               user=identity)

        services_generated += 1

    # 4) Set a given (new) framework to standstill
    data_api_client._post_with_updated_by(url='{}/frameworks/{}'.format(data_api_url, args.new_slug),
                                          data={"frameworks": {"status": "standstill"}},
                                          user=identity)

    # a) Runs the `mark-definite-framework-results.py` script to mark x suppliers as on the new framework.
    subprocess.call(['python', 'scripts/mark-definite-framework-results.py', '--reassess-failed-sf', '--updated-by',
                     identity, args.env, args.data_api_token, args.new_slug, filepath_declaration_validator])

    # b) Runs the `make-dos-live.py` script (which simply migrates draft services to 'real' services)
    subprocess.call(['python', 'scripts/make-dos-live.py', args.new_slug, args.env, args.data_api_token])

    # 6) Runs the `index-to-search-service.py` script to index the new services
    index_name = '{}-{}'.format(args.new_slug, date.today().isoformat())
    subprocess.call(['python', 'scripts/index-to-search-service.py services', '--index', index_name, '--frameworks',
                     args.new_slug, '--api-token', args.data_api_token, '--search-api-token', args.search_api_token,
                     args.env])

    # 7) Return the framework to its initial state.
    data_api_client._post_with_updated_by(url='{}/frameworks/{}'.format(data_api_url, args.new_slug),
                                          data={"frameworks": {"status": current_framework_state}},
                                          user=identity)

    print("Report:\n\n"
          "-> Services created: {}\n"
          "-> Suppliers used: {}\n"
          "---> {}\n".format(args.quantity, len(suppliers_prepared),
                             ', '.join([str(x) for x in suppliers_prepared])))
