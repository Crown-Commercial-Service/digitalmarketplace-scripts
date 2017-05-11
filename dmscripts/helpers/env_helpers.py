def get_api_endpoint_from_stage(stage, app='api'):
    """Return the full URL of given API or Search API environment.

    :param stage: environment name. Can be one of 'preview', 'staging',
                  'production' or 'dev' (aliases: 'local', 'development').
    :param app: should be either 'api' or 'search-api'

    """

    stage_domains = {
        'preview_paas': 'https://{}.preview.marketplace.team'.format(app),
        'staging_paas': 'https://{}.staging.marketplace.team'.format(app),
        'production': 'https://{}.digitalmarketplace.service.gov.uk'.format(app),
        'preview': 'https://preview-{}.development.digitalmarketplace.service.gov.uk'.format(app),
        'staging': 'https://staging-{}.digitalmarketplace.service.gov.uk'.format(app),
    }

    dev_ports = {
        'api': 5000,
        'search-api': 5001,
    }

    if stage in ['local', 'dev', 'development']:
        return 'http://localhost:{}'.format(dev_ports[app])

    return stage_domains[stage]


def get_assets_endpoint_from_stage(stage):
    return get_api_endpoint_from_stage(stage, 'assets')
