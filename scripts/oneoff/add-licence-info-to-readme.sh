#!/bin/bash
# This script will create a PR to append licence info to the README for a given repo, via the Github API.
#
# It's intended to be run locally from a developer's top level directory, containing the checked-out repos.
# You'll need the GITHUB_ACCESS_TOKEN environment variable.
#
# Note that the script changes the git config to use the dm-ssp-jenkins user - remember to change it back afterwards!
#
# Syntax: ./digitalmarketplace-scripts/scripts/oneoff/add-licence-info-to-readme.sh [repo_name]

set -e

REPO_NAME=$(echo "${1}" | tr "[:upper:]" "[:lower:]")
GIT_README_UPDATE_BRANCH_NAME=$(date +"%Y-%m-%dT%H-%M-%S-readme-licence-info")

if [ -z "${GITHUB_ACCESS_TOKEN}" ]; then
  echo "Required environment variable GITHUB_ACCESS_TOKEN is undefined."
  exit 1
fi

function create_readme_update_branch() {
  cd "${REPO_NAME}"
  git checkout master
  git checkout -b "${GIT_README_UPDATE_BRANCH_NAME}"
}

function commit_and_create_github_pr() {
  git config user.email "support@digitalmarketplace.service.gov.uk"
  git config user.name "dm-ssp-jenkins"
  git commit -a -m "$1" -m "$2"
  git push -q origin "${GIT_README_UPDATE_BRANCH_NAME}"
  post_data="{\"title\": \"$1\", \"body\": \"$2\", \"base\": \"master\", \"head\": \"${GIT_README_UPDATE_BRANCH_NAME}\"}"
  response_data=$(curl -XPOST -H "Accept: application/vnd.github.v3.full+json" -d "$post_data" "https://${GITHUB_ACCESS_TOKEN}@api.github.com/repos/Crown-Commercial-Service/${REPO_NAME}/pulls")
  echo "Created PR#$(echo "${response_data}" | jq -crM '.number') on Crown-Commercial-Service/${REPO_NAME}."
  echo "https://www.github.com/Crown-Commercial-Service/${REPO_NAME}/pull/$(echo "${response_data}" | jq -crM '.number')"
}

function add_licence_info() {
  create_readme_update_branch

  echo "Adding LICENCE info to README for ${REPO_NAME}."

  # Markdown text to be appended
  LICENCE_TEXT=$(cat <<EOF

## Licence

Unless stated otherwise, the codebase is released under [the MIT License][mit].
This covers both the codebase and any sample code in the documentation.

The documentation is [&copy; Crown copyright][copyright] and available under the terms
of the [Open Government 3.0][ogl] licence.

[mit]: LICENCE
[copyright]: http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/crown-copyright/
[ogl]: http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
EOF
  )
  echo "${LICENCE_TEXT}" >> "README.md"

  commit_and_create_github_pr "Update README with LICENCE info" "As per [GDS Way](https://gds-way.cloudapps.digital/manuals/readme-guidance.html#writing-readmes) guidelines."

  echo "Done."
}

add_licence_info
