
This test can be run against a local development instance or any environment.
However unless run only production has the declaration information needed to
generate PDFs.

  $ . $TESTDIR/setup.sh

Supplier ID from command line

  $ ./scripts/generate-framework-agreement-signature-pages.py --dry-run $DM_ENVIRONMENT g-cloud-10 $TMPDIR/output $DM_AGREEMENTS_REPO --supplier-id=710024
  * found 1 supplier records to process (glob)
  * generating framework agreement page for successful supplier 710024 (glob)

Multiple supplier IDs from command line

  $ ./scripts/generate-framework-agreement-signature-pages.py --dry-run $DM_ENVIRONMENT g-cloud-10 $TMPDIR/output $DM_AGREEMENTS_REPO --supplier-id=710024 --supplier-id=710056
  * found 2 supplier records to process (glob)
  * generating framework agreement page for successful supplier 710024 (glob)
  * generating framework agreement page for successful supplier 710056 (glob)

Supplier IDs from file

  $ cat > $TMPDIR/suppliers << EOF
  > 710028
  > 710029
  > EOF
  $ ./scripts/generate-framework-agreement-signature-pages.py --dry-run $DM_ENVIRONMENT g-cloud-10 $TMPDIR/output $DM_AGREEMENTS_REPO --supplier-ids-from=$TMPDIR/suppliers
  * found 2 supplier records to process (glob)
  * generating framework agreement page for successful supplier 710028 (glob)
  * generating framework agreement page for successful supplier 710029 (glob)

Skips failed suppliers

  $ ./scripts/generate-framework-agreement-signature-pages.py --dry-run $DM_ENVIRONMENT g-cloud-10 $TMPDIR/output $DM_AGREEMENTS_REPO --supplier-id=710026
  * found 1 supplier records to process (glob)
  * skipping supplier 710026 due to pass_fail=='fail' (glob)

Ignores suppliers without framework interest
  $ ./scripts/generate-framework-agreement-signature-pages.py --dry-run $DM_ENVIRONMENT g-cloud-10 $TMPDIR/output $DM_AGREEMENTS_REPO --supplier-id=710380
  * found 0 supplier records to process (glob)
