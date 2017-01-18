def get_api_endpoint_from_stage(stage, app='api'):
    """Return the full URL of given API or Search API environment.

    :param stage: environment name. Can be one of 'preview', 'staging',
                  'production' or 'dev' (aliases: 'local', 'development').
    :param app: should be either 'api' or 'search-api'

    """

    stage_prefixes = {
        'preview': 'preview-{}.development'.format(app),
        'staging': 'staging-{}'.format(app),
        'production': app
    }

    dev_ports = {
        'api': 5000,
        'search-api': 5001,
    }

    if stage in ['local', 'dev', 'development']:
        return 'http://localhost:{}'.format(dev_ports[app])

    return "https://{}.digitalmarketplace.service.gov.uk".format(
        stage_prefixes[stage]
    )


def get_assets_endpoint_from_stage(stage):
    return get_api_endpoint_from_stage(stage, 'assets')
