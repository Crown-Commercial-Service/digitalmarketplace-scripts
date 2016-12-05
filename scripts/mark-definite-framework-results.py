#!/usr/bin/env python
"""
Uses a number of supplied json schemas to determine whether suppliers on a particular framework should be marked as
onFramework. Attemots to recover a less strict subset of the schema from inside the declaration_definite_pass_schema
at json path definitions/notDefiniteFail. This is used to differentiate between suppliers that definitely fail and those
that will require a human decision ("discretionary"). If not found, all suppliers failing
declaration_definite_pass_schema will have onFramework left unmodified (probably remaining null).

Will also mark draft services with their respectivee validity (in the status field) as determined by
draft_service_schema.

Usage: mark-definite-framework-results.py [options] <stage> <api_token> <framework_slug>
            <declaration_definite_pass_schema_path> [<draft_service_schema_path>]

--updated-by=<user_string>        Specify updated_by string to use in API requests
--dry-run                         Don't actually perform any updates on API
--reassess-passed-sf              Don't skip supplier_frameworks with onFramework already True
--reassess-failed-sf              Don't skip supplier_frameworks with onFramework already False
--reassess-failed-draft-services  Don't skip draft_services with "failed" status
"""
# ew..
import sys
sys.path.insert(0, '.')


import getpass
import json


from dmscripts.env import get_api_endpoint_from_stage
from dmapiclient import DataAPIClient
from dmscripts.mark_definite_framework_results import mark_definite_framework_results
from dmscripts.logging import configure_logger


if __name__ == "__main__":
    from docopt import docopt
    args = docopt(__doc__)

    client = DataAPIClient(get_api_endpoint_from_stage(args["<stage>"], "api"), args["<api_token>"])
    updated_by = args["--updated-by"] or getpass.getuser()

    declaration_definite_pass_schema = json.load(open(args["<declaration_definite_pass_schema_path>"], "r"))

    declaration_not_definite_fail_schema = \
        (declaration_definite_pass_schema.get("definitions") or {}).get("notDefiniteFail")

    service_schema = json.load(
        open(args["<draft_service_schema_path>"], "r")
    ) if args["<draft_service_schema_path>"] else None

    configure_logger()

    mark_definite_framework_results(
        client,
        updated_by,
        args["<framework_slug>"],
        declaration_definite_pass_schema,
        declaration_not_definite_fail_schema=declaration_not_definite_fail_schema,
        service_schema=service_schema,
        reassess_passed=args["--reassess-passed-sf"],
        reassess_failed=args["--reassess-failed-sf"],
        reassess_failed_draft_services=args["--reassess-failed-draft-services"],
        dry_run=args["--dry-run"],
    )