#!/bin/sh

[ -n "$TESTDIR" ] && . "$TESTDIR"/../setup.sh

# Generally tests will need an API key for GOV.UK Notify
[ -n "$NOTIFY_API_KEY" ] || NOTIFY_API_KEY="this-is-not-a-real-key-but-notify-api-keys-have-to-be-74-characters-long"
