#!/bin/bash
# This script will create a PR against the dm-aws repository, setting the maintenance mode variable as appropriate.
#
# Syntax: ./scripts/maintenance-mode-pr.sh [live|maintenance|recovery] [preview|staging|production]

set -e

MODE=$(echo "${1}" | tr "[:upper:]" "[:lower:]")
STAGE=$(echo "${2}" | tr "[:lower:]" "[:upper:]")
STAGE_LOWER=$(echo "${STAGE}" | tr "[:upper:]" "[:lower:]")
GIT_MAINTENANCE_MODE_BRANCH_NAME=$(date +"%Y-%m-%dT%H-%M-%S-maintenance-mode")

if [ -z "${GITHUB_ACCESS_TOKEN}" ]; then
  echo "Required environment variable GITHUB_ACCESS_TOKEN is undefined."
  exit 1
fi

if [[ "${STAGE}" != "PREVIEW" && "${STAGE}" != "STAGING" && "${STAGE}" != "PRODUCTION" ]]; then
  echo "Syntax: ./scripts/maintenance-mode-pr.sh [live|maintenance|recovery] [preview|staging|production]"
  exit 2
fi

if [[ "${MODE}" != "live" && "${MODE}" != "maintenance" && "${MODE}" != "recovery" ]]; then
  echo "Syntax: ./scripts/maintenance-mode-pr.sh [live|maintenance|recovery] [preview|staging|production]"
  exit 2
fi

function create_maintenance_mode_branch()
{
    rm -rf digitalmarketplace-aws
    git clone "https://${GITHUB_ACCESS_TOKEN}@github.com/alphagov/digitalmarketplace-aws.git"
    cd digitalmarketplace-aws
    git checkout -b "${GIT_MAINTENANCE_MODE_BRANCH_NAME}"
}

function commit_and_create_github_pr()
{
    git config user.email "support@digitalmarketplace.service.gov.uk"
    git config user.name "dm-ssp-jenkins"
    git commit -a -m "$1" -m "$2"
    git push origin "${GIT_MAINTENANCE_MODE_BRANCH_NAME}"
    post_data="{\"title\": \"$1\", \"body\": \"$2\", \"base\": \"master\", \"head\": \"${GIT_MAINTENANCE_MODE_BRANCH_NAME}\"}"
    response_data=$(curl -XPOST -H "Accept: application/vnd.github.v3.full+json" -d "$post_data" "https://${GITHUB_ACCESS_TOKEN}@api.github.com/repos/alphagov/digitalmarketplace-aws/pulls")
    echo "Created PR#$(echo "${response_data}" | jq -crM '.number') on alphagov/digitalmarketplace-aws."
    echo "https://www.github.com/alphagov/digitalmarketplace-aws/pull/$(echo "${response_data}" | jq -crM '.number')"
}

function set_maintenance_mode()
{
    create_maintenance_mode_branch
    sed -i.bak "s/^maintenance_mode: .*$/maintenance_mode: ${MODE}/" "vars/${STAGE_LOWER}.yml"
    rm "vars/${STAGE_LOWER}.yml.bak"
    commit_and_create_github_pr "Set maintenance mode to ${MODE}" "## Summary\r\nSet maintenance mode to '${MODE}' for the ${STAGE} environment."
    echo "Done."
}

set_maintenance_mode
