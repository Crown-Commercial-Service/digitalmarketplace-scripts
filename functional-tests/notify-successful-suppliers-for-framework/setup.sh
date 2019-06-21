#!/bin/sh

[ -n "$TESTDIR" ] && . "$TESTDIR"/../setup.sh

# Generally tests will need an API key and a template for GOV.UK Notify
[ -n "$NOTIFY_API_KEY" ] || NOTIFY_API_KEY="this-is-not-a-real-key-but-notify-api-keys-have-to-be-74-characters-long"
[ -n "$NOTIFY_TEMPLATE_ID" ] || NOTIFY_TEMPLATE_ID="fake-template-id"
