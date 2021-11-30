#!/bin/bash
# This script will create a PR against the aws-nft repository, setting the NFT environemnt to use the new databse.
#
# Syntax: ./scripts/nft-database-backup-config-pr.sh [live|maintenance]

set -e

MODE=$(echo "${1}" | tr "[:upper:]" "[:lower:]")
DB_NAME="digitalmarketplace_api_db"
DB_COPY_NAME="digitalmarketplace_api_db_backup-copy"

if [ -z "${GITHUB_ACCESS_TOKEN}" ]; then
  echo "Required environment variable GITHUB_ACCESS_TOKEN is undefined."
  exit 1
fi

if [[ "${MODE}" != "live" && "${MODE}" != "maintenance" ]];
then
  echo "Syntax: ./scripts/nft-database-backup-config-pr.sh [live|maintenance]"
  exit 2
fi

if [[ $MODE == 'live' ]];
then
  GIT_MAINTENANCE_MODE_BRANCH_NAME=$(date +"%Y-%m-%dT%H-%M-%S-revert-to-main-db")
  PR_TITLE="Reverting to main DB"
  PR_BODY="Set maintenance mode to '${MODE}' for the NFT environment and change the database service to '${DB_NAME}'."
  OLD_NAME=$DB_COPY_NAME
  NEW_NAME=$DB_NAME
else
  GIT_MAINTENANCE_MODE_BRANCH_NAME=$(date +"%Y-%m-%dT%H-%M-%S-change-to-backup-db")
  PR_TITLE="Changing to DB backup"
  PR_BODY="Set maintenance mode to '${MODE}' for the NFT environment and change the database service to '${DB_COPY_NAME}'."
  OLD_NAME=$DB_NAME
  NEW_NAME=$DB_COPY_NAME
fi

function create_database_backup_branch()
{
    rm -rf digitalmarketplace-aws-nft
    git clone "https://${GITHUB_ACCESS_TOKEN}@github.com/brickendon/digitalmarketplace-aws-nft" --quiet
    cd digitalmarketplace-aws-nft
    git checkout -b "${GIT_MAINTENANCE_MODE_BRANCH_NAME}" --quiet
}

function commit_and_create_github_pr()
{
    git config user.email "ccs-digitalmarketplace+nft@crowncommercial.gov.uk" --quiet
    git config user.name "dm-nft-jenkins" --quiet
    git commit -a -m "$1" -m "$2" --quiet
    git push origin "${GIT_MAINTENANCE_MODE_BRANCH_NAME}" --quiet &> /dev/null
    post_data="{\"title\": \"$1\", \"body\": \"$2\", \"base\": \"main\", \"head\": \"${GIT_MAINTENANCE_MODE_BRANCH_NAME}\"}"
    response_data=$(curl -s -XPOST -H "Accept: application/vnd.github.v3.full+json" -d "$post_data" "https://${GITHUB_ACCESS_TOKEN}@api.github.com/repos/brickendon/digitalmarketplace-aws-nft/pulls")
    echo "https://www.github.com/brickendon/digitalmarketplace-aws-nft/pull/$(echo "${response_data}" | jq -crM '.number')"
}

function set_database()
{
    create_database_backup_branch
    sed -i.bak "s/^maintenance_mode: .*$/maintenance_mode: ${MODE}/" "vars/nft.yml"
    sed -i.bak "s/${OLD_NAME}/${NEW_NAME}/" "vars/nft.yml"
    rm "vars/nft.yml.bak"
    commit_and_create_github_pr "${PR_TITLE}" "## Summary\r\n${PR_BODY}"
}

set_database