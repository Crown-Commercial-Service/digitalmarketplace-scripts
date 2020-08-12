#!/usr/bin/env python
"""
This script is for marking suppliers as having passed/failed a framework, but it will only do so in cases where the
result can be determined "automatically" not requiring human involvement.

This is determined using a json schema (specified in arguments). This information is used to decide if a
particular supplier should be marked as onFramework. The script will attempt to recover a less strict subset of the
schema from inside the (mandatory) declaration_definite_pass_schema at its' json path definitions/baseline.
This is used to differentiate between suppliers that definitely fail and those that will require a human decision
("discretionary"). If this subschema is not found, all suppliers failing declaration_definite_pass_schema will have
onFramework left unmodified (probably remaining null).

The default behaviour is to skip supplier_frameworks which already have a non-null onFramework set, though this can be
controlled with the --reassess-passed-sf and --reassess-failed-sf flags.

You may only want to reassess certain suppliers. This can be done with the `supplier-id-file` option.
It should be set to the path to a file containing the supplier ids to check, one per line.

Usage:
    scripts/framework-applications/mark-definite-framework-results.py <stage> <framework_slug>
        <declaration_definite_pass_schema_path> [options]

--updated-by=<user_string>        Specify updated_by string to use in API requests
--dry-run                         Don't actually perform any updates on API
--reassess-passed-sf              Don't skip supplier_frameworks with onFramework already True
--reassess-failed-sf              Don't skip supplier_frameworks with onFramework already False
-v, --verbose                     Produce more detailed console output
--supplier-id-file=<path>         Path to file containing supplier ids to check. One ID per line.
--excluded-supplier-ids=<esis>    Supplier IDs to be excluded.
"""
import sys
sys.path.insert(0, '.')

import getpass
import json

from dmscripts.helpers.auth_helpers import get_auth_token
from dmapiclient import DataAPIClient
from dmscripts.mark_definite_framework_results import mark_definite_framework_results
from dmscripts.helpers.logging_helpers import configure_logger
from dmscripts.helpers.logging_helpers import INFO as loglevel_INFO, DEBUG as loglevel_DEBUG
from dmscripts.helpers.supplier_data_helpers import get_supplier_ids_from_file
from dmutils.env_helpers import get_api_endpoint_from_stage


if __name__ == "__main__":
    from docopt import docopt
    args = docopt(__doc__)

    client = DataAPIClient(get_api_endpoint_from_stage(args["<stage>"], "api"), get_auth_token('api', args['<stage>']))
    updated_by = args["--updated-by"] or getpass.getuser()

    declaration_definite_pass_schema = json.load(open(args["<declaration_definite_pass_schema_path>"], "r"))

    declaration_discretionary_pass_schema = \
        (declaration_definite_pass_schema.get("definitions") or {}).get("baseline")

    supplier_id_file = args["--supplier-id-file"]
    supplier_ids = get_supplier_ids_from_file(supplier_id_file)

    configure_logger({"script": loglevel_DEBUG if args["--verbose"] else loglevel_INFO})

    mark_definite_framework_results(
        client,
        updated_by,
        args["<framework_slug>"],
        declaration_definite_pass_schema,
        declaration_discretionary_pass_schema=declaration_discretionary_pass_schema,
        reassess_passed_suppliers=args["--reassess-passed-sf"],
        reassess_failed_suppliers=args["--reassess-failed-sf"],
        dry_run=args["--dry-run"],
        supplier_ids=supplier_ids,
        excluded_supplier_ids=args["--excluded-supplier-ids"],
    )
