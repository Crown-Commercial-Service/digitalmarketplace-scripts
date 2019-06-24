
  $ . $TESTDIR/setup.sh

Supplier ID from command line

  $ ./scripts/framework-applications/notify-successful-suppliers-for-framework.py --dry-run $DM_ENVIRONMENT g-cloud-10 $NOTIFY_API_KEY $NOTIFY_TEMPLATE_ID --supplier-id=93271
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10/suppliers?with_declarations=False finished in * (glob)
  * dmapiclient.base INFO API GET request on */users/export/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=93271&framework=g-cloud-10 finished in * (glob)
  * script INFO [Dry Run] Sending email to supplier user '*' (glob)


Multiple supplier IDs from command line

  $ ./scripts/framework-applications/notify-successful-suppliers-for-framework.py --dry-run $DM_ENVIRONMENT g-cloud-10 $NOTIFY_API_KEY $NOTIFY_TEMPLATE_ID --supplier-id=92254 --supplier-id=92778
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10/suppliers?with_declarations=False finished in * (glob)
  * dmapiclient.base INFO API GET request on */users/export/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=92254&framework=g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=92778&framework=g-cloud-10 finished in * (glob)

  $ ./scripts/framework-applications/notify-successful-suppliers-for-framework.py --dry-run $DM_ENVIRONMENT g-cloud-10 $NOTIFY_API_KEY $NOTIFY_TEMPLATE_ID --supplier-id=92254,92778
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10/suppliers?with_declarations=False finished in * (glob)
  * dmapiclient.base INFO API GET request on */users/export/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=92254&framework=g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=92778&framework=g-cloud-10 finished in * (glob)


Supplier IDs from file

  $ cat > $TMPDIR/suppliers << EOF
  > 92254
  > 93271
  > EOF
  $ ./scripts/framework-applications/notify-successful-suppliers-for-framework.py --dry-run $DM_ENVIRONMENT g-cloud-10 $NOTIFY_API_KEY $NOTIFY_TEMPLATE_ID --supplier-ids-from=$TMPDIR/suppliers
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */frameworks/g-cloud-10/suppliers?with_declarations=False finished in * (glob)
  * dmapiclient.base INFO API GET request on */users/export/g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=92254&framework=g-cloud-10 finished in * (glob)
  * dmapiclient.base INFO API GET request on */draft-services?supplier_id=93271&framework=g-cloud-10 finished in * (glob)
  * script INFO [Dry Run] Sending email to supplier user '*' (glob)
