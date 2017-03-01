from mandrill import Mandrill


def get_sent_emails(mandrill_api_key, tags, date_from=None):
    mandrill_client = Mandrill(mandrill_api_key)

    return mandrill_client.messages.search(tags=tags, date_from=date_from, limit=1000)
