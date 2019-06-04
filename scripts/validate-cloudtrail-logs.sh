#!/usr/bin/env bash
#
# Usage: validate-cloudtrail-logs.sh [options] ACCOUNT START_FROM [UP_TO]
#
# Examples:
#   validate-cloudtrail-logs.sh main '1 hour ago'
#   validate-cloudtrail-logs.sh production '2019-04-11T13:13'
#   validate-cloudtrail-logs.sh --verbose development '3 days ago' '2 days ago'
#
# Arguments:
#   ACCOUNT     The AWS account to validate logs for (e.g. main, development, backups).
#   START_FROM  A date/time to start validating logs from, can be a date relative to now.
#   UP_TO       A date/time to start validating logs from, can be a date relative to now. Defaults to now.
#
# Options:
#   --config=FILE  Path to file containing details of trails (default: $DM_CREDENTIALS_REPO/jenkins-vars/cloudtrail.yaml).
#   -n, --dry-run  Output information on command but do not run.
#   -q, --quiet    Suppress output of log validation information.
#   -v, --verbose  Print detailed script debug statements.
#   -h, --help     Show this message.

set -eo pipefail

source docopts.sh

help=$(docopt_get_help_string "$0")
eval "$(docopts -h "$help" : "$@")"

VERBOSE="${VERBOSE:-$verbose}"
$VERBOSE && set -x

[ -n "$config" ] && CONFIG_FILE="$config" || CONFIG_FILE="$DM_CREDENTIALS_REPO/jenkins-vars/cloudtrail.yaml"
[ -f "$CONFIG_FILE" ] || { echo "error: config file '$CONFIG_FILE' does not exist"; exit 1; }

[ -n "$UP_TO" ] || UP_TO="now"
START_TIME="$(date --date="$START_FROM" --utc --iso-8601=minutes)" || exit 1
END_TIME="$(date --date="$UP_TO" --utc --iso-8601=minutes)" || exit 1

export ACCOUNT
account="$("$DM_CREDENTIALS_REPO"/sops-wrapper -d --extract '["cloudtrail_validate_logs_roles"]' "$CONFIG_FILE" | yq 'map(select(.account == env.ACCOUNT))[0]')"

AWS_PROFILE="$(echo "$account" | yq -r '.profile.name')"

COMMAND="aws cloudtrail validate-logs"

COMMAND+=" --trail-arn $(echo "$account" | yq -r '.trail_arn')"
COMMAND+=" --start-time $START_TIME"
[ -n "$END_TIME" ] && COMMAND+=" --end-time $END_TIME"

if ! $QUIET
then
  COMMAND+=" --verbose"
fi

export AWS_PROFILE
echo AWS_PROFILE="$AWS_PROFILE" $COMMAND
$dry_run && exit

# run command, echo output to terminal, exit with non-zero status if any logs are invalid
$COMMAND | tee /dev/stderr | (! grep -q INVALID)
