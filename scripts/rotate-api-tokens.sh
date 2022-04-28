#!/bin/bash
# This script will update Data, Search and Antivirus API tokens for a given environment. It does this by checking out the
# dm-credentials repository, decrypting the relevant creds files and using 'yq' (a yaml CLI editor) to inject new
# tokens. These are committed and pushed up, then the GitHub API is used to create a pull request for the developer
# to manually approve.
#
# If running locally you will need to provide AWS_PROFILE=sops or equivalent.
# If running locally through Docker, you will probably also need to mount your ~/.aws folder at `/root/.aws` for SOPS to be able to decrypt credentials. But be careful with this due to file permissions.
# If running on Jenkins, AWS allows SOPS to decrypt credentials using its EC2 instance profile - even within Docker.
#
# Syntax: ./scripts/rotate-api-tokens.sh [add-new|remove-old|add-new-callback|remove-old-callback|change-ft-account-passwords|sync-ft-account-passwords|create-new-aws-token|deactivate-old-aws-token] [preview|staging|production]

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
  echo "Syntax: ./scripts/rotate-api-tokens.sh [add-new|remove-old|add-new-callback|remove-old-callback|change-ft-account-passwords|sync-ft-account-passwords|create-new-aws-token|deactivate-old-aws-token] [preview|staging|production]"
  exit 2
fi

function generate_api_token() {
  echo $(python3 -c "import random, string; print(''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(${1:-56})))")
}

function get_jenkins_env_token_name() {
  if [[ "$1" == "api" ]]; then
    app_name="DATA_API"
  elif [[ "$1" == "search_api" ]]; then
    app_name="SEARCH_API"
  elif [[ "$1" == "antivirus_api" ]]; then
    app_name="ANTIVIRUS_API"
  else
    exit 3
  fi

  echo "DM_${app_name}_TOKEN_${STAGE}"
}

function create_credentials_update_branch() {
  rm -rf digitalmarketplace-credentials
  git clone "https://${GITHUB_ACCESS_TOKEN}@github.com/Crown-Commercial-Service/digitalmarketplace-credentials.git"
  cd digitalmarketplace-credentials
  git checkout -b "${GIT_CREDS_UPDATE_BRANCH_NAME}"
}

function commit_and_create_github_pr() {
  git config user.email "support@digitalmarketplace.service.gov.uk"
  git config user.name "dm-ssp-jenkins"
  git commit -a -m "$1" -m "$2"
  git push -q origin "${GIT_CREDS_UPDATE_BRANCH_NAME}"
  post_data="{\"title\": \"$1\", \"body\": \"$2\", \"base\": \"master\", \"head\": \"${GIT_CREDS_UPDATE_BRANCH_NAME}\"}"
  response_data=$(curl -XPOST -H "Accept: application/vnd.github.v3.full+json" -d "$post_data" "https://${GITHUB_ACCESS_TOKEN}@api.github.com/repos/Crown-Commercial-Service/digitalmarketplace-credentials/pulls")
  echo "Created PR#$(echo "${response_data}" | jq -crM '.number') on Crown-Commercial-Service/digitalmarketplace-credentials."
  echo "https://www.github.com/Crown-Commercial-Service/digitalmarketplace-credentials/pull/$(echo "${response_data}" | jq -crM '.number')"
}

function add_new_tokens() {
  create_credentials_update_branch

  echo "Adding three new tokens (Application, Jenkins, Developer) to the Data-API, Search-API and Antivirus-API for ${STAGE}."

  # Insert three new tokens for the api, search-api and antivirus-api, and update Jenkins config with the new jenkins token.
  for api_type in api search_api antivirus_api; do
    app_token="A$(generate_api_token)"
    jenkins_token="J$(generate_api_token)"
    dev_token="D$(generate_api_token)"

    # Add the tokens for the Data/Search/Antivirus APIs
    ./sops-wrapper --set "[\"${api_type}\"] $(./sops-wrapper -d vars/${STAGE_LOWER}.yaml | yq -crM '.'${api_type}'.auth_tokens |= ["'${app_token}'", "'${jenkins_token}'", "'${dev_token}'"] + . | .'${api_type})" "vars/${STAGE_LOWER}.yaml"

    # Update the tokens for Jenkins
    ./sops-wrapper --set "[\"jenkins_env_variables\"] $(./sops-wrapper -d jenkins-vars/jenkins.yaml | yq -crM '.jenkins_env_variables.'$(get_jenkins_env_token_name ${api_type})' = "'${jenkins_token}'" | .jenkins_env_variables')" jenkins-vars/jenkins.yaml
  done

  commit_and_create_github_pr "Add new API tokens" "## Summary\r\nInsert three new Data, Search and Antivirus API tokens (application, jenkins, developer) for the ${STAGE} environment in order to recycle the existing tokens."

  echo "Done."
}

function remove_old_tokens() {
  create_credentials_update_branch

  echo "Removing all tokens except the three newest (Application, Jenkins, Developer) from the Data-API and Search-API for ${STAGE}."

  for api_type in api search_api antivirus_api; do
    # Remove all except the first three Data/Search/Antivirus API tokens
    ./sops-wrapper --set "[\"${api_type}\"] $(./sops-wrapper -d vars/${STAGE_LOWER}.yaml | yq -crM '.'${api_type}'.auth_tokens = .'${api_type}'.auth_tokens[:3] | .'${api_type})" vars/${STAGE_LOWER}.yaml
  done

  commit_and_create_github_pr "Remove old API tokens" "## Summary\r\nRemove all old Data, Search and Antivirus API tokens for the ${STAGE} environment, leaving just the latest three (application, jenkins, developer)."

  echo "Done."
}

function add_new_callback_token() {
  create_credentials_update_branch

  echo "Adding a new token for Notify callbacks to the Data-API for ${STAGE}."

  api_type="api"
  callback_token="N$(generate_api_token)"
  new_api_data=$(./sops-wrapper -d vars/${STAGE_LOWER}.yaml|yq -crM '.'${api_type}'.callback_auth_tokens |= ["'${callback_token}'"] + . | .'${api_type})
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

function change_ft_account_passwords() {
  create_credentials_update_branch

  echo "Changing Functional Test DMP account passwords for ${STAGE}."

  admin_manager_pass_path=pass/digitalmarketplace.service.gov.uk/admin-manager
  export STAGE_LOWER

  if [[ $STAGE_LOWER = "production" ]] ; then
    # if we're changing the admin manager password, we're also going to have to update it in $admin_manager_pass_path,
    # so note the email address to look out for
    admin_manager_email=$(./sops-wrapper -d $admin_manager_pass_path | sed -En -e "s/^login:\s+//p")
  fi

  # find all values of fields named _email which have an equivalent _password variable
  for ACCOUNT_EMAIL in $(./sops-wrapper -d jenkins-vars/jenkins.yaml|yq -crM '[[(.smoulder_test_variables, .smoke_test_variables, .functional_test_variables)[env.STAGE_LOWER]|values|to_entries]|flatten|.[]|select(.key|endswith("_email")).value]|unique|.[]') ; do
    export ACCOUNT_EMAIL
    # passwords for a particular email address need to be common across test variants becuase they
    # share the same instance. limit to 40 chars because our frontends attempt to enforce a limit of... 50? - let's not
    # complicate things.
    new_password=$(generate_api_token 40)

    for VARIANT in smoulder_test_variables smoke_test_variables functional_test_variables ; do
      export VARIANT
      # for each field ending in _password whose equivalent _email-ending field has the value $ACCOUNT_EMAIL
      for password_field in  $(./sops-wrapper -d jenkins-vars/jenkins.yaml|yq -crM '.[env.VARIANT][env.STAGE_LOWER] as $vars|$vars|to_entries|.[]|select((.key|endswith("_email")) and .value == env.ACCOUNT_EMAIL).key|sub("_email$"; "_password")|select($vars[.])') ; do
        ./sops-wrapper --set "[\"${VARIANT}\"][\"${STAGE_LOWER}\"][\"${password_field}\"] \"${new_password}\"" jenkins-vars/jenkins.yaml
      done
    done

    if [[ $STAGE_LOWER = "production" && $admin_manager_email = $ACCOUNT_EMAIL ]] ; then
      # also update this password in $admin_manager_pass_path - it's the same account
      ./sops-wrapper -d $admin_manager_pass_path | tail -n +2 | cat <(echo $new_password) - | ./sops-wrapper -e /dev/stdin > $admin_manager_pass_path.tmp
      # sops doesn't like reading & writing to the same file at the same time
      mv $admin_manager_pass_path.tmp $admin_manager_pass_path
    fi
  done

  commit_and_create_github_pr "Change functional test DMP account passwords for ${STAGE}" "## Summary\r\nChanges all functional test/smoke test/smoulder test DMP account passwords for ${STAGE}.\r\n\r\nOnce this is merged you will want to get a move on with synchronizing with jenkins and the DMP accounts as smoke tests will likely be broken until this process is complete."

  echo "Done."
}

function sync_ft_account_passwords() {

  if [ -z "${DM_CREDENTIALS_REPO}" ]; then
    echo "Required environment variable DM_CREDENTIALS_REPO is undefined."
    exit 1
  fi

  echo "Synchronizing Functional Test DMP account passwords for ${STAGE}."

  # a piece of magic from https://stackoverflow.com/a/246128 to determine the location of this bash script (so
  # we can find its sibling python script
  source_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
  already_seen=()
  export STAGE STAGE_LOWER DM_CREDENTIALS_REPO

  for VARIANT in smoulder_test_variables smoke_test_variables functional_test_variables ; do
    export VARIANT
    for EMAIL_FIELD in $(${DM_CREDENTIALS_REPO}/sops-wrapper -d ${DM_CREDENTIALS_REPO}/jenkins-vars/jenkins.yaml|yq -crM '.[env.VARIANT][env.STAGE_LOWER] as $vars|$vars|values|keys|.[]|select(endswith("_email"))|select($vars[.|sub("_email$"; "_password")])') ; do
      export EMAIL_FIELD
      export ACCOUNT_EMAIL=$(${DM_CREDENTIALS_REPO}/sops-wrapper -d ${DM_CREDENTIALS_REPO}/jenkins-vars/jenkins.yaml|yq -crM '.[env.VARIANT][env.STAGE_LOWER][env.EMAIL_FIELD]')

      # bash does not have a real "array contains" test. not kidding.
      if [[ ! " ${already_seen[*]} " =~ " ${ACCOUNT_EMAIL} " ]]; then
        export ACCOUNT_PASSWORD=$(${DM_CREDENTIALS_REPO}/sops-wrapper -d ${DM_CREDENTIALS_REPO}/jenkins-vars/jenkins.yaml|yq -crM '.[env.VARIANT][env.STAGE_LOWER][env.EMAIL_FIELD|sub("_email"; "_password")]')

        echo "Setting password for ${ACCOUNT_EMAIL}"
        $source_dir/set-user-password-by-email-address.py || [[ $? = 2 ]]  # continue if account wasn't found

        already_seen+=($ACCOUNT_EMAIL)
      else
        echo "Already set ${ACCOUNT_EMAIL}"
      fi
    done
  done

  echo "Done."
}

function get_aws_profile() {
  if [[ $STAGE == "PREVIEW" ]]
  then
    echo "development-infrastructure"
  else
    echo "production-infrastructure"
  fi
}

function create_new_aws_token() {
  aws_profile_name="$(get_aws_profile)"
  if [[ $STAGE == "PREVIEW" ]]
  then
    credentials_files=(vars/preview.yaml)
  else
    credentials_files=(vars/production.yaml vars/staging.yaml)
  fi

  inactive_token_id="$(AWS_PROFILE=$aws_profile_name aws iam list-access-keys --user-name paas-app | jq -r '.AccessKeyMetadata[] | select(.Status =="Inactive") | .AccessKeyId')"
  if [[ -n "$inactive_token_id" ]]
  then
    echo "Deleting old inactive token: $inactive_token_id"
    AWS_PROFILE=$aws_profile_name aws iam delete-access-key --user-name paas-app --access-key-id "$inactive_token_id"
  fi

  if [[ $(AWS_PROFILE=$aws_profile_name aws iam list-access-keys --user-name paas-app  | jq -r '.AccessKeyMetadata | length') != "1" ]]
  then
    echo "Unable to rotate multiple active access tokens"
    exit 1
  fi

  new_token_pair="$(AWS_PROFILE=$aws_profile_name aws iam create-access-key --user-name paas-app)"
  new_access_token_id="$(echo "$new_token_pair" | jq -r '.AccessKey.AccessKeyId')"
  new_access_token_secret="$(echo "$new_token_pair" | jq -r '.AccessKey.SecretAccessKey')"

  create_credentials_update_branch
  for credential_file in "${credentials_files[@]}"
  do
    ./sops-wrapper --set "[\"aws_access_key_id\"] \"${new_access_token_id}\"" "${credential_file}"
    ./sops-wrapper --set "[\"aws_secret_access_key\"] \"${new_access_token_secret}\"" "${credential_file}"
  done

  commit_and_create_github_pr "Rotate AWS access token for ${STAGE}" "## Summary\r\nSwitch to new AWS access token for ${STAGE}.\r\n\r\nOnce this is merged, re-release all apps in the affected environments. Follows the process in https://crown-commercial-service.github.io/digitalmarketplace-manual/2nd-line-runbook/rotate-keys.html#rotating-aws-access-keys."

  echo "Done."
}

function deactivate_old_aws_token() {
  aws_profile_name="$(get_aws_profile)"
  credentials_file="vars/${STAGE_LOWER}.yaml"

  create_credentials_update_branch
  live_access_key_id="$(./sops-wrapper -d "$credentials_file" | yq ".aws_access_key_id")"

  unused_access_key_id="$(AWS_PROFILE=$aws_profile_name aws iam list-access-keys --user-name paas-app | jq -r ".AccessKeyMetadata[] | select(.Status == \"Active\") | select (.AccessKeyId != ${live_access_key_id}) | .AccessKeyId")"
  if [[ -n "$unused_access_key_id" ]]
  then
    echo "Deactivating old access token: $unused_access_key_id"
    AWS_PROFILE=$aws_profile_name aws iam update-access-key --user-name paas-app --access-key-id "$unused_access_key_id" --status Inactive
  fi

  echo "Done."
}

case ${COMMAND} in
  ADD-NEW) add_new_tokens;;
  REMOVE-OLD) remove_old_tokens;;
  ADD-NEW-CALLBACK) add_new_callback_token;;
  REMOVE-OLD-CALLBACK) remove_old_callback_token;;
  CHANGE-FT-ACCOUNT-PASSWORDS) change_ft_account_passwords;;
  SYNC-FT-ACCOUNT-PASSWORDS) sync_ft_account_passwords;;
  CREATE-NEW-AWS-TOKEN) create_new_aws_token;;
  DEACTIVATE-OLD-AWS-TOKEN) deactivate_old_aws_token;;
  *) echo "Syntax: ./scripts/rotate-api-tokens.sh [add-new|remove-old|add-new-callback|remove-old-callback|change-ft-account-passwords|sync-ft-account-passwords|create-new-aws-token|deactivate-old-aws-token] [preview|staging|production]";;
esac
