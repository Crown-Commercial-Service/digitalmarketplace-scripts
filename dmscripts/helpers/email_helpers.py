from functools import partial

from dmutils.email import DMNotifyClient


DEFAULT_REDIRECT_DOMAINS = {
    "example.com": "success@simulator.amazonses.com",
    "example.gov.uk": "success@simulator.amazonses.com",
    "user.marketplace.team": "success@simulator.amazonses.com",
}


scripts_notify_client = partial(DMNotifyClient, redirect_domains_to_address=DEFAULT_REDIRECT_DOMAINS)
