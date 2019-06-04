
  $ . $TESTDIR/setup.sh

  $ # set up testing stubs for the 'aws cloudtrail validate-logs' command
  $ ln $(which aws) $TMPDIR/stubs/aws-original
  $ touch $TMPDIR/stubs/aws-stub
  $ cat > $TMPDIR/stubs/aws << 'EOF'
  > #!/bin/sh
  > if [ "$1 $2" = "cloudtrail validate-logs" ]; then
  >   exec $TMPDIR/stubs/aws-stub
  > else
  >   exec aws-original $@
  > fi
  > EOF
  $ chmod +x $TMPDIR/stubs/aws $TMPDIR/stubs/aws-stub $TMPDIR/stubs/aws-original

validate-cloudtrail-logs echoes the output of the AWS cli.

  $ cat > $TMPDIR/stubs/aws-stub << EOF
  > #!/bin/sh
  > echo 'test stderr output' >&2
  > echo 'test stdout output'
  > EOF
  $ ./scripts/validate-cloudtrail-logs.sh $AWS_ACCOUNT now
  AWS_PROFILE=* aws cloudtrail validate-logs * (glob)
  test stderr output
  test stdout output

validate-cloudtrail-logs exits with non-zero status if AWS cli reports invalid logs.

  $ cat > $TMPDIR/stubs/aws-stub << EOF
  > #!/bin/sh
  > echo 'INVALID'
  > EOF
  $ ./scripts/validate-cloudtrail-logs.sh $AWS_ACCOUNT now
  AWS_PROFILE=* aws cloudtrail validate-logs * (glob)
  INVALID
  [1]

validate-cloudtrail-logs exits with non-zero status if AWS cli exits with non-zero status.

  $ cat > $TMPDIR/stubs/aws-stub << EOF
  > #!/bin/sh
  > exit 2
  > EOF
  $ ./scripts/validate-cloudtrail-logs.sh $AWS_ACCOUNT now
  AWS_PROFILE=* aws cloudtrail validate-logs * (glob)
  [2]
