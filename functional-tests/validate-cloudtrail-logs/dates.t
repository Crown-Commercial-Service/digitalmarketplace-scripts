
  $ . $TESTDIR/setup.sh
  $ [ -n "$FAKETIME" ] || FAKETIME="2019-05-06T12:13:54Z"
  $ command -v faketime >/dev/null 2>&1 || { >&2 echo "This test requires faketime but it is not installed. Skipping." ; exit 80; }
  $ alias validate-cloudtrail-logs="faketime '$FAKETIME' bash ./scripts/validate-cloudtrail-logs.sh"

validate-cloudtrail-logs requires at least one date, the time for the earliest log to validate. By default it will look at any logs up to the time of invocation.

  $ validate-cloudtrail-logs -n $AWS_ACCOUNT '2019-06-07T09:00Z'
  AWS_PROFILE=*-cloudtrail-validate-logs aws cloudtrail validate-logs --trail-arn arn:aws:cloudtrail:*:*:trail/*-cloudtrail --start-time 2019-06-07T09:00+00:00 --end-time 2019-05-06T12:13+00:00 (glob)

You can also specify an end date

  $ validate-cloudtrail-logs -n $AWS_ACCOUNT '2019-05-07T09:00Z' '2019-06-07T09:00Z'
  AWS_PROFILE=*-cloudtrail-validate-logs aws cloudtrail validate-logs --trail-arn arn:aws:cloudtrail:*:*:trail/*-cloudtrail --start-time 2019-05-07T09:00+00:00 --end-time 2019-06-07T09:00+00:00 (glob)

Either date can be described in a human readable way

  $ validate-cloudtrail-logs -n $AWS_ACCOUNT '10am 1 month ago' '10am today'
  AWS_PROFILE=*-cloudtrail-validate-logs aws cloudtrail validate-logs --trail-arn arn:aws:cloudtrail:*:*:trail/*-cloudtrail --start-time 2019-04-06T10:00+00:00 --end-time 2019-05-06T10:00+00:00 (glob)

If the date can't be parsed the script will exit with an error

  $ validate-cloudtrail-logs -n $AWS_ACCOUNT 'last thermidor' '10am today'
  date: invalid date 'last thermidor'
  [1]
