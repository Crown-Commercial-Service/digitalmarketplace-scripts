#!/usr/bin/env python

"""
For a given framework, this script generates a CSV file for the supplier declaration and questions in the 'edit
submission' manifest. Questions can be filtered by supplying a context (for example to include questions in one
particular lot).

The order of fields in the generated file is:
"Page title", "Question", "Hint", "Answer 1", "Answer 2", ...

Before running this you will need to:
pip install -r requirements.txt

Usage:
    scripts/generate-questions-csv.py <DM-content-root-dir> <output-directory> --framework=<slug> [--context=<yaml>]

-h --help    show this message

Example:
    scripts/generate-questions-csv.py /path/to/dm-frameworks/ ~ --framework=g-cloud-9 --context="lot: SaaS"
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmcontent.content_loader import ContentLoader
from dmscripts.generate_questions_csv import generate_csv
import yaml

if __name__ == '__main__':
    arguments = docopt(__doc__)

    path_to_manifest = arguments['<DM-content-root-dir>']
    content_loader = ContentLoader(path_to_manifest)

    output_directory = arguments['<output-directory>']
    framework_slug = arguments.get('--framework')

    context_string = arguments.get('--context')
    context = yaml.safe_load(context_string) if context_string else None

    generate_csv(output_directory, framework_slug, content_loader, context)
