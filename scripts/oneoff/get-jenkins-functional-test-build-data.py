#!/usr/bin/env python
"""
Export build time and status for for functional test runs on preview and staging.

You must set DM_JENKINS_API_USER and DM_JENKINS_API_TOKEN environment variables to authenticate to the API.
DM_JENKINS_API_USER is your Github username and you can generate an API token at
https://ci.marketplace.team/user/your-user-name/configure

Usage: ./scripts/oneoff/get-jenkins-functional-test-build-data.py [--filename=<file>]

Options:
    --help, -h                  Show this information
    --filename=<file>           Optional. The output filename to use. Defaults to 'functional_test_report.csv'
"""

import os
import csv
import logging
import requests
from requests.auth import HTTPBasicAuth
from docopt import docopt
from typing import Dict, List, Any

Build = Dict[str, Any]


def get_job_build_data(job: str, auth: HTTPBasicAuth) -> List[Build]:
    """
    Get build timestamp, status and duration for every build Jenkins has saved for this job.
    """
    logging.info(f"Getting build data for job: {job}")
    response = requests.get(
        f"https://ci.marketplace.team/job/{job}/api/json?tree=builds[id,timestamp,result,duration]{{1,}}",
        auth=auth
    )
    response.raise_for_status()
    return response.json()["builds"]


def format_build(job: str, build: Build) -> Build:
    """
    Add the job name, stage and URL to the build dict and format the duration in seconds
    """
    stage = job.split("-")[-1]
    build["job"] = job
    build["stage"] = stage
    build["link"] = f"https://ci.marketplace.team/job/{job}/{build['id']}/"
    build["duration"] = build["duration"] / 1000
    del build["_class"]
    return build


if __name__ == "__main__":
    args = docopt(__doc__)
    logging.basicConfig(level=logging.INFO)

    FT_JOB_NAMES = ["functional-tests-preview", "functional-tests-staging"]
    API_USER = os.getenv("DM_JENKINS_API_USER")
    API_TOKEN = os.getenv("DM_JENKINS_API_TOKEN")

    OUTPUT_FILE = args.get("<file>") or "functional_test_report.csv"

    auth = HTTPBasicAuth(API_USER, API_TOKEN)

    build_data = []
    for job in FT_JOB_NAMES:
        for build in get_job_build_data(job, auth):
            build_data.append(format_build(job, build))

    logging.info(f"Writing report to {OUTPUT_FILE}")
    headers = build_data[0].keys()
    with open(OUTPUT_FILE, "w") as f:
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        writer.writerows(build_data)
