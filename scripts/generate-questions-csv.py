"""
This script generates a CSV file for the supplier declaration and questions in each lot for a specified framework.

The order of fields in the generated file is:
"Page title", "Question", "Hint", "Answer 1", "Answer 2", ...

Before running this you will need to:
pip install -r requirements.txt

Usage:
    scripts/generate-questions-csv.py <path_to_manifest> <output_directory> --framework=<slug>
"""
import sys
sys.path.insert(0, '.')

from docopt import docopt
from dmutils.content_loader import ContentLoader
from dmscripts.generate_questions_csv import generate_csv

if __name__ == '__main__':
    arguments = docopt(__doc__)

    path_to_manifest = arguments['<path_to_manifest>']
    content_loader = ContentLoader(path_to_manifest)

    output_directory = arguments['<output_directory>']
    framework_slug = arguments.get('--framework')

    generate_csv(output_directory, framework_slug, content_loader)
