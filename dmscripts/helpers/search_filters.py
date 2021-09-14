from typing import List
from collections import OrderedDict

from dmcontent.content_loader import ContentManifest


# the following functions were copied from the buyer frontend with minor alterations
# https://github.com/Crown-Commercial-Service/digitalmarketplace-buyer-frontend/blob/a83163/app/main/presenters/search_presenters.py
def sections_for_lot(lot_slug: str, manifest: ContentManifest, all_lots: List[dict]):
    if lot_slug == 'all':
        for lot_slug in [x["slug"] for x in all_lots]:
            manifest = manifest.filter({'lot': lot_slug})
    else:
        manifest = manifest.filter({'lot': lot_slug})

    return manifest.sections


# the below functions were copied from buyer frontend, with modifications
# https://github.com/Crown-Commercial-Service/digitalmarketplace-buyer-frontend/blob/a83163/app/main/helpers/search_helpers.py#L180
def get_filter_value_from_question_option(option):
    return option.get("value", option.get("label", ""))


def filters_for_lot(lot_slug: str, manifest: ContentManifest, all_lots: List[dict]):
    sections = sections_for_lot(lot_slug, manifest, all_lots=all_lots)
    lot_filters: OrderedDict[str, dict] = OrderedDict()

    for section in sections:
        section_filter = {
            "label": section["name"],
            "slug": section["slug"],
            "filters": [],
        }
        for question in section["questions"]:
            section_filter["filters"].extend(
                _filters_for_question(question)
            )

        lot_filters[section.slug] = section_filter

    return lot_filters


def _filters_for_question(question):
    question_filters = []
    if question['type'] == 'boolean':
        question_filters.append({
            'label': question.get('filter_label') or question.get('name') or question['question'],
            'name': question['id'],
            'id': question['id'],
            'value': 'true',
        })

    elif question['type'] in ['checkboxes', 'radios', 'checkbox_tree']:
        _recursive_add_option_filters(question, question['options'], question_filters)

    return question_filters


def _recursive_add_option_filters(question, options_list, filters_list):
    for option in options_list:
        if not option.get('filter_ignore'):
            value = get_filter_value_from_question_option(option)
            presented_filter = {
                'label': option.get('filter_label') or option['label'],
                'name': question['id'],
                'id': '{}-{}'.format(
                    question['id'],
                    value.replace(' ', '-')),
                'value': value,
            }
            if option.get('options'):
                presented_filter['children'] = []
                _recursive_add_option_filters(question, option.get('options', []), presented_filter['children'])

            filters_list.append(presented_filter)
