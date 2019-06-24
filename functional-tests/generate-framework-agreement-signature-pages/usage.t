
Script must be run from digitalmarketplace-scripts repo directory.

  $ cd $TESTDIR/../..

Usage:

  $ ./scripts/framework-applications/generate-framework-agreement-signature-pages.py
  Usage:
      scripts/framework-applications/generate-framework-agreement-signature-pages.py
          [-v...] [options]
          <stage> <framework> <output_dir> <agreements_repo>
          [--supplier-id=<id>... | --supplier-ids-from=<file>]
      scripts/framework-applications/generate-framework-agreement-signature-pages.py (-h | --help)
  [1]


Invalid arguments:

  $ ./scripts/framework-applications/generate-framework-agreement-signature-pages.py --do-the-thing garbage
  Usage:
      scripts/framework-applications/generate-framework-agreement-signature-pages.py
          [-v...] [options]
          <stage> <framework> <output_dir> <agreements_repo>
          [--supplier-id=<id>... | --supplier-ids-from=<file>]
      scripts/framework-applications/generate-framework-agreement-signature-pages.py (-h | --help)
  [1]

Detailed help:

  $ ./scripts/framework-applications/generate-framework-agreement-signature-pages.py -h
  Generate framework agreement signature pages from supplier "about you"
  information for suppliers who successfully applied to a framework.
  
  Usage:
      scripts/framework-applications/generate-framework-agreement-signature-pages.py
          [-v...] [options]
          <stage> <framework> <output_dir> <agreements_repo>
          [--supplier-id=<id>... | --supplier-ids-from=<file>]
      scripts/framework-applications/generate-framework-agreement-signature-pages.py (-h | --help)
  
  Options:
      <stage>                     Environment to run script against.
      <framework>                 Slug of framework to generate agreements for.
      <output_dir>                Path to folder where script will save output.
      <agreements_repo>           Path to folder containing framework templates.
  
      --supplier-id=<id>          ID of supplier to generate agreement page for.
      --supplier-ids-from=<file>  Path to file containing supplier IDs, one per line.
  
      -h, --help                  Show this help message
  
      -n, --dry-run               Run script without generating files.
      -t <n>, --threads=<n>       Number of threads to use, if not supplied the
                                  script will be run without threading.
      -v, --verbose               Show debug log messages.
  
      If neither `--supplier-ids-from` or `--supplier-id` are provided then
      framework agreements will be generated for all valid suppliers.
  
  PREREQUISITE: You'll need wkhtmltopdf installed for this to work
  (http://wkhtmltopdf.org/)
  
  As well as calling out to the Digital Marketplace api, this script uses the
  online countries register.
  
  PDF signature pages are generated for all suppliers that have a framework
  interest and at least one completed draft service.
