
This test can be run against any environment with a recent database dump.
See the test readme for details.

  $ . $TESTDIR/setup.sh

Successful suppliers should have signature page in output folder

  $ ./scripts/generate-framework-agreement-signature-pages.py $DM_ENVIRONMENT g-cloud-10 $TMPDIR/output $DM_AGREEMENTS_REPO --supplier-id=710024 --supplier-id=710038 2> $TMPDIR/err.log || cat $TMPDIR/err.log
  $ ls $TMPDIR/output
  710024-signature-page.pdf
  710038-signature-page.pdf

Signature pages should be valid PDFs of a reasonable size

  $ cd $TMPDIR/output
  $ file *
  710024-signature-page.pdf: PDF document, version 1.4
  710038-signature-page.pdf: PDF document, version 1.4
  $ du -h *
   24K	710024-signature-page.pdf
   24K	710038-signature-page.pdf
