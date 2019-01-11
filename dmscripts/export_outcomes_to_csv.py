import csv


def _deep_getitem(toplevel, key_chain):
    """
        dig down into toplevel object using successive keys in key_chain until doing so fails (in which case return
        None) or we run out of keys (in which case return the end result)
    """
    current = toplevel
    try:
        for key in key_chain:
            current = current[key]
        return current
    except (TypeError, IndexError, KeyError):
        return None


_default_deep_fieldnames = (
    "id",
    "completedAt",
    "result",
    "resultOfDirectAward.project.id",
    "resultOfDirectAward.search.id",
    "resultOfDirectAward.archivedService.service.id",
    "resultOfFurtherCompetition.brief.id",
    "resultOfFurtherCompetition.briefResponse.id",
    "award.startDate",
    "award.endDate",
    "award.awardingOrganisationName",
    "award.awardValue",
)


def export_outcomes_to_csv(data_api_client, fileobj, deep_fieldnames=_default_deep_fieldnames):
    csv_dwriter = csv.DictWriter(fileobj, deep_fieldnames)
    csv_dwriter.writeheader()

    for outcome_dict in data_api_client.find_outcomes_iter(completed=True):
        csv_dwriter.writerow({
            deep_fieldname: _deep_getitem(outcome_dict, deep_fieldname.split("."))
            for deep_fieldname in deep_fieldnames
        })
