
import random


def get_supplier_id(api_client, framework, lot):
    services = [
        s for s in api_client.find_services(framework=framework, lot=lot)['services']
        if s['status'] in ['published']
    ]

    if not services:
        raise RuntimeError(
            "No live services found for '{}' framework{}".format(
                framework,
                " and '{}' lot".format(lot) if lot else "",
            )
        )

    return random.choice(services)['supplierId']


def get_random_buyer_with_brief(api_client, framework, lot, *, brief_status=None):
    if brief_status is None:
        brief_status = "live,cancelled,unsuccessful,closed,awarded"

    briefs = api_client.find_briefs(
        framework=framework,
        lot=lot,
        status=brief_status,
        with_users=True,
    )["briefs"]

    if not briefs:
        raise RuntimeError(
            "No users with published briefs found for '{}' framework{}".format(
                framework,
                " and '{}' lot".format(lot) if lot else "",
            )
        )

    brief = random.choice(briefs)

    return random.choice(brief["users"])


def get_random_user(api_client, role, supplier_id=None):
    return random.choice([
        u for u in api_client.find_users(role=role, supplier_id=supplier_id)['users']
        if u['active'] and not u['locked']
    ])
