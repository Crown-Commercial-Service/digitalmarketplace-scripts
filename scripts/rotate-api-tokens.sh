#!/bin/bash
# This script will update Data and Search API tokens for a given environment. It does this by checking out the
# dm-credentials repository, decrypting the relevant creds files and using 'yq' (a yaml CLI editor) to inject new
# tokens. These are committed and pushed up, then the GitHub API is used to create a pull request for the developer
# to manually approve.
#
# If running locally you will need to provide AWS_PROFILE=sops or equivalent.
# If running locally through Docker, you will probably also need to mount your ~/.aws folder at `/root/.aws` for SOPS to be able to decrypt credentials. But be careful with this due to file permissions.
# If running on Jenkins, AWS allows SOPS to decrypt credentials using its EC2 instance profile - even within Docker.
#
# Syntax: ./scripts/rotate-api-tokens.sh [add-new|remove-old] [preview|staging|production]

set -e

COMMAND=$(echo "${1}" | tr "[:lower:]" "[:upper:]")
STAGE=$(echo "${2}" | tr "[:lower:]" "[:upper:]")
STAGE_LOWER=$(echo "${STAGE}" | tr "[:upper:]" "[:lower:]")
GIT_CREDS_UPDATE_BRANCH_NAME=$(date +"%Y-%m-%dT%H-%M-%S-credentials-update")

if [ -z "${GITHUB_ACCESS_TOKEN}" ]; then
  echo "Required environment variable GITHUB_ACCESS_TOKEN is undefined."
  exit 1
fi

if [[ "${STAGE}" != "PREVIEW" && "${STAGE}" != "STAGING" && "${STAGE}" != "PRODUCTION" ]]; then
  echo "Syntax: ./scripts/rotate-api-tokens.sh [add-new|remove-old] [preview|staging|production]"
  exit 2
fi

function generate_api_token() {
  echo $(python3 -c "import random, string; print(''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(56)))")
}

function get_jenkins_env_token_name() {
  if [[ "$1" == "api" ]]; then
    app_name="DATA_API"
  elif [[ "$1" == "search_api" ]]; then
    app_name="SEARCH_API"
  else
    exit 3
  fi

  echo "DM_${app_name}_TOKEN_${STAGE}"
}

function create_credentials_update_branch() {
  rm -rf digitalmarketplace-credentials
  git clone "https://${GITHUB_ACCESS_TOKEN}@github.com/alphagov/digitalmarketplace-credentials.git"
  cd digitalmarketplace-credentials
  git checkout -b "${GIT_CREDS_UPDATE_BRANCH_NAME}"
}

function commit_and_create_github_pr() {
  git config user.email "support@digitalmarketplace.service.gov.uk"
  git config user.name "dm-ssp-jenkins"
  git commit -a -m "$1" -m "$2"
  git push origin "${GIT_CREDS_UPDATE_BRANCH_NAME}"
  post_data="{\"title\": \"$1\", \"body\": \"$2\", \"base\": \"master\", \"head\": \"${GIT_CREDS_UPDATE_BRANCH_NAME}\"}"
  response_data=$(curl -XPOST -H "Accept: application/vnd.github.v3.full+json" -d "$post_data" "https://${GITHUB_ACCESS_TOKEN}@api.github.com/repos/alphagov/digitalmarketplace-credentials/pulls")
  echo "Created PR#$(echo "${response_data}" | jq -crM '.number') on alphagov/digitalmarketplace-credentials."
  echo "https://www.github.com/alphagov/digitalmarketplace-credentials/pull/$(echo "${response_data}" | jq -crM '.number')"
}

function add_new_tokens() {
  create_credentials_update_branch

  echo "Adding three new tokens (Application, Jenkins, Developer) to the Data-API and Search-API for ${STAGE}."

  # Insert three new tokens for the api and search-api, and update Jenkins config with the new jenkins token.
  for api_type in api search_api; do
    app_token="A$(generate_api_token)"
    jenkins_token="J$(generate_api_token)"
    dev_token="D$(generate_api_token)"

    # Add the tokens for the Data/Search API
    ./sops-wrapper --set "[\"${api_type}\"] $(./sops-wrapper -d vars/${STAGE_LOWER}.yaml | yq -crM '.'${api_type}'.auth_tokens |= ["'${app_token}'", "'${jenkins_token}'", "'${dev_token}'"] + . | .'${api_type})" "vars/${STAGE_LOWER}.yaml"

    # Update the tokens for Jenkins
    ./sops-wrapper --set "[\"jenkins_env_variables\"] $(./sops-wrapper -d jenkins-vars/jenkins.yaml | yq -crM '.jenkins_env_variables.'$(get_jenkins_env_token_name ${api_type})' = "'${jenkins_token}'" | .jenkins_env_variables')" jenkins-vars/jenkins.yaml
  done

  commit_and_create_github_pr "Add new API tokens" "## Summary\r\nInsert three new Data and Search API tokens (application, jenkins, developer) for the ${STAGE} environment in order to recycle the existing tokens."

  echo "Done."
}

function remove_old_tokens() {
  create_credentials_update_branch

  echo "Removing all tokens except the three newest (Application, Jenkins, Developer) from the Data-API and Search-API for ${STAGE}."

  for api_type in api search_api; do
    # Remove all except the first three Data/Search API tokens
    ./sops-wrapper --set "[\"${api_type}\"] $(./sops-wrapper -d vars/${STAGE_LOWER}.yaml | yq -crM '.'${api_type}'.auth_tokens = .'${api_type}'.auth_tokens[:3] | .'${api_type})" vars/${STAGE_LOWER}.yaml
  done

  commit_and_create_github_pr "Remove old API tokens" "## Summary\r\nRemove all old Data and Search API tokens for the ${STAGE} environment, leaving just the latest three (application, jenkins, developer)."

  echo "Done."
}

function add_new_callback_token() {
  create_credentials_update_branch

  echo "Adding a new token for Notify callbacks to the Data-API for ${STAGE}."

  api_type="api"
  callback_token="N$(generate_api_token)"
  new_api_data=$(./sops-wrapper -d vars/preview.yaml|yq -crM '.'${api_type}'.callback_auth_tokens |= ["'${callback_token}'"] + . | .'${api_type})
  ./sops-wrapper --set "[\"${api_type}\"] ${new_api_data}" "vars/${STAGE_LOWER}.yaml"

  commit_and_create_github_pr "Add new callback token" "## Summary\r\nInserts a new callback token to the Data API for the ${STAGE} environment in order to recycle the existing token."

  echo "Done."
}

function remove_old_callback_token() {
  create_credentials_update_branch

  echo "Removing the old Notify callback token from the Data-API for ${STAGE}."

  api_type="api"
  new_api_data=$(./sops-wrapper -d vars/${STAGE_LOWER}.yaml | yq -crM '.'${api_type}'.callback_auth_tokens = .'${api_type}'.callback_auth_tokens[:1] | .'${api_type})
  ./sops-wrapper --set "[\"${api_type}\"] ${new_api_data}" "vars/${STAGE_LOWER}.yaml"

  commit_and_create_github_pr "Remove old callback token" "## Summary\r\nRemove the old callback token from the Data API for the ${STAGE} environment, leaving just the latest one."

  echo "Done."
}

case ${COMMAND} in
  ADD-NEW) add_new_tokens;;
  REMOVE-OLD) remove_old_tokens;;
  ADD-NEW-CALLBACK) add_new_callback_token;;
  REMOVE-OLD-CALLBACK) remove_old_callback_token;;
  *) echo "Syntax: ./scripts/rotate-api-tokens.sh [add-new|remove-old|add-new-callback|remove-old-callback] [preview|staging|production]";;
esac
