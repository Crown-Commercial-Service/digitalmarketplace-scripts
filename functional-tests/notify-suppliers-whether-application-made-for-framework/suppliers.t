
  $ . $TESTDIR/setup.sh

Supplier ID from command line

  $ ./scripts/notify-suppliers-whether-application-made-for-framework.py --dry-run $DM_ENVIRONMENT g-cloud-10 $NOTIFY_API_KEY --supplier-id=93271
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10/suppliers?with_declarations=False finished in * (glob)
  * dmapiclient.base INFO API GET request on */users/export/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=93271&framework=g-cloud-10 finished in * (glob)
  * script INFO [Dry Run] Supplier '93271' (glob)
  * script INFO [Dry Run] Sending 'application_made' email to supplier '93271' user '*' (glob)


Multiple supplier IDs from command line

  $ ./scripts/notify-suppliers-whether-application-made-for-framework.py --dry-run $DM_ENVIRONMENT g-cloud-10 $NOTIFY_API_KEY --supplier-id=92254 --supplier-id=92778
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10/suppliers?with_declarations=False finished in * (glob)
  * dmapiclient.base INFO API GET request on */users/export/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=92254&framework=g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=92778&framework=g-cloud-10 finished in * (glob)
  * script INFO [Dry Run] Supplier '92254' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92254' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92254' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92254' user '*' (glob)
  * script INFO [Dry Run] Supplier '92778' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92778' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92778' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92778' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92778' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92778' user '*' (glob)

  $ ./scripts/notify-suppliers-whether-application-made-for-framework.py --dry-run $DM_ENVIRONMENT g-cloud-10 $NOTIFY_API_KEY --supplier-id=92254,92778
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10/suppliers?with_declarations=False finished in * (glob)
  * dmapiclient.base INFO API GET request on */users/export/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=92254&framework=g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=92778&framework=g-cloud-10 finished in * (glob)
  * script INFO [Dry Run] Supplier '92254' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92254' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92254' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92254' user '*' (glob)
  * script INFO [Dry Run] Supplier '92778' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92778' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92778' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92778' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92778' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92778' user '*' (glob)

Supplier IDs from file

  $ cat > $TMPDIR/suppliers << EOF
  > 92254
  > 93271
  > EOF
  $ ./scripts/notify-suppliers-whether-application-made-for-framework.py --dry-run $DM_ENVIRONMENT g-cloud-10 $NOTIFY_API_KEY --supplier-ids-from=$TMPDIR/suppliers
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10/suppliers?with_declarations=False finished in * (glob)
  * dmapiclient.base INFO API GET request on */users/export/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=92254&framework=g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=93271&framework=g-cloud-10 finished in * (glob)
  * script INFO [Dry Run] Supplier '92254' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92254' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92254' user '*' (glob)
  * script INFO [Dry Run] Sending 'application_not_made' email to supplier '92254' user '*' (glob)
  * script INFO [Dry Run] Supplier '93271' (glob)
  * script INFO [Dry Run] Sending 'application_made' email to supplier '93271' user '*' (glob)
