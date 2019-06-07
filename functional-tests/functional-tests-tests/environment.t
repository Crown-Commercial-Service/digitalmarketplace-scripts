
  $ . $TESTDIR/../setup.sh

Trying to run functional tests against production will result in the test being skipped and a message being printed to the user.

  $ DM_ENVIRONMENT=production cram -q functional-tests/functional-tests-tests/environment.t
  s
  # Ran 1 tests, 1 skipped, 0 failed.
