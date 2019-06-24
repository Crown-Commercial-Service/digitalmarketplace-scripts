
  $ . $TESTDIR/setup.sh

validate-cloudtrail-logs expects a config file that is normally found in the credentials repo.
You can override the config file path, but it will complain if it can't find it.

  $ ./scripts/validate-cloudtrail-logs.sh --config=not-a-file $AWS_ACCOUNT now
  error: config file 'not-a-file' does not exist
  [1]
