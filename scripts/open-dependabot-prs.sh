#!/usr/bin/env bash
set -eu
# A script to run through all Dependabot PRs: https://trello.com/c/ElfBwilG/609-resolve-dependabot-prs
# It will open them all in your default browser.

# gh needs to be installed - see https://github.com/cli/cli#installation
gh --version > /dev/null

repos=(
  alphagov/digitalmarketplace-admin-frontend
  alphagov/digitalmarketplace-antivirus-api
  alphagov/digitalmarketplace-api
  alphagov/digitalmarketplace-apiclient
  alphagov/digitalmarketplace-briefs-frontend
  alphagov/digitalmarketplace-brief-responses-frontend
  alphagov/digitalmarketplace-buyer-frontend
  alphagov/digitalmarketplace-scripts
  alphagov/digitalmarketplace-search-api
  alphagov/digitalmarketplace-supplier-frontend
  alphagov/digitalmarketplace-user-frontend
  alphagov/digitalmarketplace-aws
  alphagov/digitalmarketplace-utils
  alphagov/digitalmarketplace-runner
  alphagov/digitalmarketplace-jenkins
  alphagov/digitalmarketplace-visual-regression
  alphagov/digitalmarketplace-govuk-frontend
  alphagov/digitalmarketplace-router
)

for repo in ${repos[@]}; do
  dependabot_prs=$(gh pr list --repo $repo | grep 'dependabot' | awk '{print $1}')

  for pr in ${dependabot_prs[@]}; do
    gh pr view --web --repo $repo $pr
  done
done
