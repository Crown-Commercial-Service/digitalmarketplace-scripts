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

import sys
import os
import csv
import logging
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth
from docopt import docopt
from dmapiclient import DataAPIClient
from dmutils.env_helpers import get_api_endpoint_from_stage
from typing import Dict, List, Any

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token

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


def format_build(job: str, build: Build, frameworks: List[dict]) -> Build:
    """
    Add the job name, stage and URL to the build dict and format the duration in seconds
    """
    stage = job.split("-")[-1]
    build["job"] = job
    build["stage"] = stage
    build["link"] = f"https://ci.marketplace.team/job/{job}/{build['id']}/"
    build["duration"] = build["duration"] / 1000
    build["framework_state"] = get_framework_state(build["timestamp"], frameworks)
    del build["_class"]
    return build


def get_framework_state(timestamp: int, frameworks: List[dict]) -> str:
    """
    Match a timestamp onto a framework state based on the opening and closing dates for each framework
    in `framework_dates`. Only record open, pending and live states.
    """
    event_time = datetime.fromtimestamp(timestamp / 1000)
    framework_states = []

    for framework in frameworks:
        if event_time > datetime.strptime(framework["frameworkExpiresAtUTC"], "%Y-%m-%dT%H:%M:%S.%fZ"):
            # expired, don't record
            pass

        elif event_time > datetime.strptime(framework["frameworkLiveAtUTC"], "%Y-%m-%dT%H:%M:%S.%fZ"):
            # This framework was still live
            framework_states.append(f"{framework['name']}: live")

        elif event_time > datetime.strptime(framework["applicationsCloseAtUTC"], "%Y-%m-%dT%H:%M:%S.%fZ"):
            framework_states.append(f"{framework['name']}: pending")

        else:
            # We don't have anything in the API response that says when a framework opens, so if it exists
            # and hasn't met any other conditions, assume it's open.
            framework_states.append(f"{framework['name']}: open")

    return " - ".join(framework_states)


if __name__ == "__main__":
    args = docopt(__doc__)
    logging.basicConfig(level=logging.INFO)

    FT_JOB_NAMES = ["functional-tests-preview", "functional-tests-staging"]
    API_USER = os.getenv("DM_JENKINS_API_USER")
    API_TOKEN = os.getenv("DM_JENKINS_API_TOKEN")

    OUTPUT_FILE = args.get("<file>") or "functional_test_report.csv"

    auth = HTTPBasicAuth(API_USER, API_TOKEN)

    # Use staging to get the framework dates because it'll be the same as production
    api_client = DataAPIClient(get_api_endpoint_from_stage("staging"), get_auth_token("api", "staging"))
    frameworks = api_client.find_frameworks()["frameworks"]

    build_data = []
    for job in FT_JOB_NAMES:
        for build in get_job_build_data(job, auth):
            build_data.append(format_build(job, build, frameworks))

    logging.info(f"Writing report to {OUTPUT_FILE}")
    headers = build_data[0].keys()
    with open(OUTPUT_FILE, "w") as f:
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        writer.writerows(build_data)
