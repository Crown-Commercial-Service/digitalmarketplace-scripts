#!/usr/bin/env python
"""Generate a TSV file for Acrobat to use as the data source for the framework agreement PDFs

Produces the successful.txt file containing all the successful suppliers, in a TSV format, arranged
to fit the fields in the framework agreeement PDFs.

Usage:
    scripts/generate-pdf-import-data.py <framework_slug> <document_type> <input_file> <output_dir>
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmscripts.generate_pdf_import_data import generate_import_data

if __name__ == '__main__':
    arguments = docopt(__doc__)

    FRAMEWORK_SLUG = arguments['<framework_slug>']
    DOCUMENT_TYPE = arguments['<document_type>']
    SUCCESSFUL_SUPPLIERS_FILE = arguments['<input_file>']
    AGREEMENTS_IMPORT_DATA_DIR = arguments['<output_dir>']

    generate_import_data(
        SUCCESSFUL_SUPPLIERS_FILE, AGREEMENTS_IMPORT_DATA_DIR, FRAMEWORK_SLUG, DOCUMENT_TYPE)
