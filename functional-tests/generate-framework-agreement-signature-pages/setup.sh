#!/bin/sh

. "$TESTDIR"/../setup.sh

# generate-framework-agreement-signature-pages generally requires the
# agreements repo
[ -n "$DM_AGREEMENTS_REPO" ] || DM_AGREEMENTS_REPO="$DM_SCRIPTS_REPO/../digitalmarketplace-agreements"

