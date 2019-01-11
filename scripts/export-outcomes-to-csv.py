#!/usr/bin/env python
"""Export outcome information from API

At time of writing, this only includes outcomes of "direct awards", because "further competition" outcomes have their
own way of being recorded for now. However this is designed with further competition awards in mind and these should
be automatically included in these exports once the data exists in the API.

<output_filename> can be substituted for a single dash ("-") in which case the output will be sent to stdout.

Usage:
    scripts/export-outcomes-to-csv.py [-h] <stage> <output_filename>

Options:
    -h --help
"""
from contextlib import contextmanager
import logging
import sys
sys.path.insert(0, '.')

from docopt import docopt

from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage

from dmscripts.helpers import logging_helpers
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.export_outcomes_to_csv import export_outcomes_to_csv


@contextmanager
def _stdout_context_manager():
    yield sys.stdout


if __name__ == "__main__":
    args = docopt(__doc__)

    logger = logging_helpers.configure_logger({"dmapiclient": logging.INFO})
    api_client = DataAPIClient(get_api_endpoint_from_stage(args["<stage>"]), get_auth_token("api", args["<stage>"]))

    filename = args["<output_filename>"]

    with _stdout_context_manager() if filename == "-" else open(filename, "w") as outfile:
        export_outcomes_to_csv(api_client, outfile)
