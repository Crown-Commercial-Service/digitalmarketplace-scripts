#!/usr/bin/env python

"""
For a given framework, this script generates CSV files for the supplier declaration and service questions.

The order of fields in the generated file is:
"Page title", "Question", "Hint", "Answer 1", "Answer 2", ...

Usage:
    scripts/framework-applications/generate-questions-csv.py <DM-content-root-dir> <output-dir> --framework=<slug>
    [options]

Options:
  --question-set=<question-set-type> i.e. one of 'declaration' or 'services' (omit to generate both)
  -h --help    show this message

Example:
    scripts/generate-questions-csv.py /path/to/dm-frameworks/ ~/output/ \
--framework=g-cloud-9 --question-set=services
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmcontent.content_loader import ContentLoader
from dmscripts.generate_questions_csv import generate_csv


G_CLOUD_LOTS = [
    'cloud-hosting',
    'cloud-software',
    'cloud-support',
]
DOS_LOTS = [
    'digital-outcomes',
    'digital-specialists',
    'user-research-participants',
    'user-research-studios',
]

QUESTION_SETS = ['declaration', 'services']


if __name__ == '__main__':
    arguments = docopt(__doc__)

    content_path = arguments['<DM-content-root-dir>']
    content_loader = ContentLoader(content_path)

    output_dir = arguments['<output-dir>']
    framework_slug = arguments.get('--framework')

    # Generate all files if --question-set not given
    question_sets = [arguments.get('--question-set')] if arguments.get('--question-set') else QUESTION_SETS

    for question_set in question_sets:
        if question_set == 'declaration':
            output_file = "{}/{}-declaration-questions.csv".format(output_dir, framework_slug)
            generate_csv(output_file, framework_slug, content_loader, question_set, context=None)
        else:
            lots = G_CLOUD_LOTS if framework_slug.startswith('g-cloud') else DOS_LOTS
            for lot in lots:
                output_file = "{}/{}-{}-service-questions.csv".format(output_dir, framework_slug, lot)
                generate_csv(output_file, framework_slug, content_loader, question_set, context={"lot": lot})
