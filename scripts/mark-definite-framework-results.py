#!/usr/bin/env python
"""
This script is for marking suppliers as having passed/failed a framework, but it will only do so in cases where the
result can be determined "automatically" not requiring human involvement.

This is determined using a number of json schemas (specified in arguments). This information is used to decide if a
particular supplier should be marked as onFramework. The script will attempt to recover a less strict subset of the
schema from inside the (mandatory) declaration_definite_pass_schema at its' json path definitions/baseline.
This is used to differentiate between suppliers that definitely fail and those that will require a human decision
("discretionary"). If this subschema is not found, all suppliers failing declaration_definite_pass_schema will have
onFramework left unmodified (probably remaining null).

If draft_service_schema is supplied, this script will also determine the result of individual draft services associated
with the supplier_framework and mark those that fail the draft_service_schema as "failed".

supplier_frameworks with no remaining non-failed draft services are considered a definite fail in all cases.

The default behaviour is to skip supplier_frameworks which already have a non-null onFramework set and draft services
whose status is already "failed", though this can be controlled with the --reassess-passed-sf, --reassess-failed-sf
and --reassess-failed-draft-services, the latter of which will mark "failed" services back as "submitted" if it proves
not to fail this time around (or if no draft_service_schema is supplied). You may only want to reassess certain
suppliers. This can be done with the `supplier-id-file` option. It should be set to the path to a file containing the
supplier ids to check, one per line.

Usage: mark-definite-framework-results.py [options] <stage> <framework_slug>
            <declaration_definite_pass_schema_path> [<draft_service_schema_path>]

--updated-by=<user_string>        Specify updated_by string to use in API requests
--dry-run                         Don't actually perform any updates on API
--reassess-passed-sf              Don't skip supplier_frameworks with onFramework already True
--reassess-failed-sf              Don't skip supplier_frameworks with onFramework already False
--reassess-failed-draft-services  Don't skip draft_services with "failed" status
-v, --verbose                     Produce more detailed console output
--supplier-id-file=<path>         Path to file containing supplier ids to check. One ID per line.
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

    service_schema = json.load(
        open(args["<draft_service_schema_path>"], "r")
    ) if args["<draft_service_schema_path>"] else None

    supplier_id_file = args["--supplier-id-file"]
    supplier_ids = get_supplier_ids_from_file(supplier_id_file)

    configure_logger({"script": loglevel_DEBUG if args["--verbose"] else loglevel_INFO})

    mark_definite_framework_results(
        client,
        updated_by,
        args["<framework_slug>"],
        declaration_definite_pass_schema,
        declaration_discretionary_pass_schema=declaration_discretionary_pass_schema,
        service_schema=service_schema,
        reassess_passed=args["--reassess-passed-sf"],
        reassess_failed=args["--reassess-failed-sf"],
        reassess_failed_draft_services=args["--reassess-failed-draft-services"],
        dry_run=args["--dry-run"],
        supplier_ids=supplier_ids,
    )
