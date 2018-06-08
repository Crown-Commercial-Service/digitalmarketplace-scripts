from functools import partial

from mandrill import Mandrill

from dmutils.email import DMNotifyClient


DEFAULT_REDIRECT_DOMAINS = {
    "example.com": "success@simulator.amazonses.com",
    "example.gov.uk": "success@simulator.amazonses.com",
    "user.marketplace.team": "success@simulator.amazonses.com",
}


scripts_notify_client = partial(DMNotifyClient, redirect_domains_to_address=DEFAULT_REDIRECT_DOMAINS)


def get_sent_emails(mandrill_api_key, tags, date_from=None):
    mandrill_client = Mandrill(mandrill_api_key)

    return mandrill_client.messages.search(tags=tags, date_from=date_from, limit=1000)
