#!/bin/sh

# Common setup for functional tests.

# Most of the scripts require that they are run from the
# digitalmarketplace-scripts repo directory.

[ -n "$DM_SCRIPTS_REPO" ] || [ -n "$TESTDIR" ] && DM_SCRIPTS_REPO="$TESTDIR" || DM_SCRIPTS_REPO=`pwd`

if ! (echo "$DM_SCRIPTS_REPO" | grep -q "digitalmarketplace-scripts"); then
  1>&2 echo "Error: could not find directory digitalmarketplace-scripts"
  exit 2
fi

while [ "`basename "$DM_SCRIPTS_REPO"`" != "digitalmarketplace-scripts" ]; do
	DM_SCRIPTS_REPO="`dirname "$DM_SCRIPTS_REPO"`"
done

cd "$DM_SCRIPTS_REPO" || exit 2

# If environment is not specified tests will try local instance.

[ -n "$DM_ENVIRONMENT" ] || DM_ENVIRONMENT="local"
[ "$DM_ENVIRONMENT" = "production" ] && { >/dev/tty echo "Running functional tests against production is not allowed; skipping"; exit 80; }
[ "$DM_ENVIRONMENT" = "local" ] || "$DM_CREDENTIALS_REPO"/sops-wrapper -v > /dev/null
