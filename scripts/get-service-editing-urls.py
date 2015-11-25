#!/usr/bin/env python
"""
Get service editing urls for each page in DOS service flow.

Usage:
    scripts/get-service-editing-urls.py <framework_location>

"""
from dmutils import content_loader
from docopt import docopt


def main(framework_location):
    lots = ['digital-outcomes', 'digital-specialists', 'user-research-studios',
            'user-research-participants']
    loader = content_loader.ContentLoader(framework_location)
    loader.load_manifest('digital-outcomes-and-specialists', 'services', 'edit_submission')
    manifest = loader.get_manifest('digital-outcomes-and-specialists', 'edit_submission')

    url = '/suppliers/frameworks/{framework_slug}/submissions/{lot_slug}/{service_id}'
    for lot in lots:
        print(lot)
        manifest_filtered = manifest.filter({'lot': lot})
        for section in manifest_filtered:
            print(url.format(framework_slug='digital-outcomes-and-specialists',
                  lot_slug=lot, service_id=section['id']))

if __name__ == '__main__':
    arguments = docopt(__doc__)
    main(arguments['<framework_location>'])
