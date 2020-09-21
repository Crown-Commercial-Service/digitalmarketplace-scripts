#!/usr/bin/env python
"""
Experimental script to provide an alternative method of manually updating draft services, for example if a user
has accessibility issues that prevent them using the site, they could submit their answers to us via CSV.

- Look up draft service ID by service name
- Map question numbers to content loader service questions for the lot
- Construct JSON blob of answers to attempt to update API
- Output validation errors
- If service has no further validation errors, output success message 'can be marked as complete'

Usage: update_draft_service_via_csv <framework> <stage> [options]

Options:
    --folder=<folder>                                     Folder to bulk-upload files
    --create-draft                                        Create new service from CSV
    --dry-run                                             List actions that would have been taken
    -h, --help                                            Show this screen

"""
import sys
import os
import csv
from dmapiclient.data import DataAPIClient
from dmapiclient import HTTPError

sys.path.insert(0, '.')
from dmscripts.helpers.auth_helpers import get_auth_token
from dmscripts.generate_questions_csv import get_questions
from dmscripts.helpers.file_helpers import get_all_files_of_type
from dmcontent.content_loader import ContentLoader
from dmutils.env_helpers import get_api_endpoint_from_stage
from docopt import docopt


LOT_ANSWER_COUNTS = {
    'cloud-support': 10,
    'cloud-hosting': 22,
    'cloud-software': 42
}

PRICE_UNITS = [
    "per unit",
    "per person",
    "per licence",
    "per user",
    "per device",
    "per instance",
    "per server",
    "per virtual machine",
    "per transaction",
    "per megabyte",
    "per gigabyte",
    "per terabyte"
]

PRICE_INTERVAL_UNITS = [
    "per second",
    "per minute",
    "per hour",
    "per day",
    "per week",
    "per quarter",
    "per 6 months",
    "per year"
]


def _normalise_service_name(name):
    return name.lower().replace('-', '').replace(' ', '').replace('/', ':').replace('.csv', '')


def get_question_objects(content):
    question_objs = {
        # 'Question text': question_obj
    }

    for section in content.sections:
        for question in get_questions(section.questions):
            question_objs[question.get_source('question')] = question

    return question_objs


def find_draft_id_by_service_name(client, supplier_id, service_name, framework_slug):
    normalised_name = _normalise_service_name(service_name)

    drafts = client.find_draft_services_by_framework_iter(framework_slug, supplier_id=supplier_id)
    matches = []
    for draft in drafts:
        if draft.get('serviceName'):
            if _normalise_service_name(draft['serviceName']) == normalised_name:
                matches.append(draft['id'])
    if len(matches) == 0:
        print(f"Unable to find Draft ID from service name {service_name}")
        return None

    if len(matches) > 1:
        print(f"Unable to find Draft ID from service name {service_name} - multiple matches")
        return 'multi'

    print("Found draft service ID", matches[0])
    return matches[0]


def get_price_data(answers):
    formatted_answers = []
    for a in answers:
        # Get rid of any rogue £ signs
        formatted_answers.append(a.replace("£", ""))
    price_dict = {
        'priceMin': formatted_answers[0]
    }

    # Parse the mandatory/optional arguments and convert to schema-friendly values
    for answer in formatted_answers[1:]:
        if answer in PRICE_UNITS:
            price_dict['priceUnit'] = answer.replace('per ', '').title()
        elif answer in PRICE_INTERVAL_UNITS:
            price_dict['priceInterval'] = answer.replace('per ', '').title()
        else:
            price_dict['priceMax'] = answer

    return price_dict


def lookup_question_id_and_text(row, questions):
    try:
        question_text = row['Question']
    except KeyError:
        print(f'Could not find row titles.')
        return None, None

    # Handle curly apostrophes removed from CSV
    if "'" in question_text:
        question_text = question_text.replace("'", "’")

    # Lookup long-winded question text in global question_objects to get camelCase ID
    try:
        question_id = questions[question_text].id
    except KeyError:
        print(f'Could not find question {row["Question"]}')
        return None, None

    return question_id, question_text


def parse_answer_from_csv_row(row, questions, question_text, lot_slug):
    answers = [row[f"Answer {i + 1}"] for i in range(0, LOT_ANSWER_COUNTS[lot_slug]) if row.get(f"Answer {i + 1}")]

    if not answers:
        # Question has been left blank
        return None

    if question_text == 'Which categories does your service fit under?':
        return answers

    if question_text == 'How much does the service cost (excluding VAT)?':
        # Price answer can be up to 4 fields - add to JSON in create_draft_json_from_csv()
        price_dict = get_price_data(answers)
        return price_dict

    if hasattr(questions[question_text], 'options') and questions[question_text].options:
        # Check if the answer(s) need to be mapped to another value
        mapped_answers = []
        for answer in answers:
            for option_dict in questions[question_text].options:
                # handle curly apostrophes in option labels
                formatted_answer = answer.replace("'", "’")
                if option_dict['label'] in [formatted_answer, answer]:
                    # Service categories don't have an option value - use original answers
                    mapped_answers.append(option_dict.get('value', answer))

        if questions[question_text].type in ['radios']:
            # Log warning if multiple options chosen
            if mapped_answers and len(mapped_answers) > 1:
                print("Multiple answers given for radio button - using first answer", question_text)

            # Only 1 option allowed - use the first
            mapped_answers = mapped_answers[0] if mapped_answers else None

        return mapped_answers

    if questions[question_text].type in ['list', 'checkboxes']:
        # Multipart answer that doesn't need mapping
        return answers

    # Otherwise treat as a single answer
    answer = answers[0]

    # Check if answer needs to be mapped to another value
    if hasattr(questions[question_text], 'options') and questions[question_text].options:
        for option_dict in questions[question_text].options:
            # handle curly apostrophes in option labels
            formatted_answer = answer.replace("'", "’")
            if option_dict['label'] in [formatted_answer, answer]:
                answer = option_dict.get('value', answer)

    # Convert booleans to JSON true/false
    if questions[question_text].type == 'boolean':
        answer = True if answer == 'Yes' else False
        # Log warning if multiple options chosen
        if len(answers) > 1:
            print("Multiple answers given for boolean question")

    return answer


def create_draft_json_from_csv(filepath, lot_slug, question_objects, encoding=None):
    # Parse rows from CSV and build a JSON dict
    draft_json = {}

    with open(filepath, encoding=encoding) as f:
        reader = csv.DictReader(f)

        for row in reader:
            question_id, question_text = lookup_question_id_and_text(row, question_objects)
            if not question_id:
                continue

            answer = parse_answer_from_csv_row(row, question_objects, question_text, lot_slug)
            if answer is not None:
                if question_id == 'price':
                    # Add all price fields
                    draft_json.update(answer)
                elif 'serviceCategories' in question_id:
                    if question_id in draft_json:
                        draft_json[question_id].extend(answer)
                    else:
                        draft_json[question_id] = answer
                    # Remove duplicates
                    categories = draft_json[question_id]
                    draft_json[question_id] = list(sorted(set(categories)))
                else:
                    draft_json[question_id] = answer

    return draft_json


def output_service_categories_features_and_benefits_summary(draft_json):
    # Useful for determining if these fields are over the max word limit per item
    print("Service categories count:", len(draft_json.get('serviceCategories', [])))

    for question_key in ['serviceFeatures', 'serviceBenefits']:
        print(f"{question_key}:", draft_json.get(question_key))
        for item in draft_json.get(question_key, []):
            words_per_items = len(item.split(' '))
            if words_per_items > 10:
                print("Max words per item exceeded")
                print("{} ({} words)".format(item, words_per_items))


def split_lot_and_service(lot_and_service_name):
    lot_slug, service_name = None, None
    for lot in LOT_ANSWER_COUNTS.keys():
        if lot in lot_and_service_name:
            lot_slug = lot
            service_name = lot_and_service_name.split(lot_slug)[1][1:]
            break

    if not lot_slug:
        print(f"Unable to identify lot for {lot_and_service_name}")
        return None, None

    service_name = service_name.replace('.csv', '')

    return lot_slug, service_name


def output_results(unidentifiable_files, malformed_csvs, successful_draft_ids, failed_draft_ids):
    # Output successful / failed draft IDs
    print(len(successful_draft_ids), "successful draft services")
    if successful_draft_ids:
        with open('successful-csv-draft-ids.txt', 'w') as f:
            for s, f_, d in successful_draft_ids:
                f.write(f"{s}, {f_}, {d}" + '\n')

    if failed_draft_ids:
        print(len(failed_draft_ids), "failed draft services")
        with open('failed-csv-draft-ids.txt', 'w') as f:
            for s, f_, d, exc in failed_draft_ids:
                f.write(f"{s}, {f_}, {d}, {exc}" + '\n')

    # Output CSVs that we couldn't parse
    if malformed_csvs:
        print(len(malformed_csvs), "malformed CSVs")
        with open('malformed-csv-draft-ids.txt', 'w') as f:
            for s, d in malformed_csvs:
                f.write(f"{s}, {d}" + '\n')

    # Output CSVs we couldn't match to a draft service
    if unidentifiable_files:
        print(len(unidentifiable_files), "unidentifiable files")
        with open('unidentifiable-draft-service-files.txt', 'w') as f:
            for d in unidentifiable_files:
                f.write(str(d) + '\n')


def update_draft_services_from_folder(folder_name, api_client, framework_slug, content_loader, dry_run, create_draft):
    failed_draft_ids = []
    successful_draft_ids = []
    unidentifiable_files = []
    malformed_csvs = []

    content_loader.load_manifest(framework_slug, 'services', 'edit_submission')
    content = content_loader.get_manifest(framework_slug, 'edit_submission')

    for filepath in get_all_files_of_type(folder_name, 'csv'):
        file_name = os.path.basename(filepath)
        print(file_name)
        # Get supplier ID from filename
        # supplier_id, lot_and_service_name = file_name.split('-', maxsplit=1)
        supplier_id = os.path.basename(filepath.split('/')[-2][:-9])
        lot_and_service_name = file_name
        print(f"Supplier ID {supplier_id}")

        print(lot_and_service_name)
        lot_slug, service_name = split_lot_and_service(lot_and_service_name)
        if not (lot_slug and service_name):
            unidentifiable_files.append(file_name)
            continue

        print(lot_slug)
        print(service_name)
        # Get the id
        if create_draft:
            initial_data = {"serviceName": service_name}
            try:
                draft = api_client.create_new_draft_service(
                    framework_slug, lot_slug, supplier_id, initial_data,
                    f"{framework_slug} create draft service script"
                )
                id_ = draft['services']['id']
            except HTTPError as e:
                print(f'WARNING: {e}')
                malformed_csvs.append((supplier_id, e))
        else:
            id_ = find_draft_id_by_service_name(api_client, supplier_id, service_name, framework_slug)
            if id_ is None or id_ == 'multi':
                unidentifiable_files.append(file_name)
                continue

        # Get a dict of service questions for the lot, where the key matches the question text in the CSVs
        content = content.filter(context={"lot": lot_slug})
        question_objects_ = get_question_objects(content)

        # Only then bother trying to parse CSV into JSON
        try:
            draft_json = create_draft_json_from_csv(filepath, lot_slug, question_objects_)
        except UnicodeDecodeError:
            print("WARNING:", "unable to decode CSV using utf-8, trying cp1252")
            try:
                draft_json = create_draft_json_from_csv(filepath, lot_slug, question_objects_, encoding="cp1252")
            except UnicodeDecodeError as e:
                print("WARNING:", e)
                malformed_csvs.append((supplier_id, file_name))
                continue
        except KeyError as e:
                print("WARNING:", e)
                malformed_csvs.append((supplier_id, file_name))
                continue

        # Try updating service data
        if dry_run:
            # Log something
            print(f"Would update draft ID {id_} with some JSON:")
            print(draft_json)
            successful_draft_ids.append((supplier_id, file_name, id_))
        else:
            for section in content.sections:
                questions = section.get_field_names()
                section_json = {
                    q: draft_json[q] for q in questions if q in draft_json
                }
                try:
                    if section_json:
                        api_client.update_draft_service(
                            id_,
                            section_json,
                            f'{framework_slug} service update script',
                            page_questions=questions
                        )
                except HTTPError as exc:
                    # Unable to update section
                    print(f"Section '{section.name}' for Draft ID {id_} failed.")
                    print(section_json)
                    print(str(exc))

            # Once all sections updated, check for remaining validation errors
            draft = api_client.get_draft_service(id_)
            if draft['validationErrors']:
                print(f"Draft ID {id_} Validation errors:")
                errors = {k: v for k, v in draft['validationErrors'].items() if k != '_form'}
                failed_draft_ids.append((supplier_id, file_name, id_, errors))
                # Debugging serviceCategories, serviceBenefits, serviceFeatures
                output_service_categories_features_and_benefits_summary(draft_json)
            else:
                print(f"Draft ID {id_} ready to be marked as complete.")
                successful_draft_ids.append((supplier_id, file_name, id_))

    output_results(unidentifiable_files, malformed_csvs, successful_draft_ids, failed_draft_ids)


if __name__ == "__main__":
    arguments = docopt(__doc__)

    # Get script arguments
    framework_slug = arguments['<framework>']
    stage = arguments['<stage>'] or 'local'
    dry_run = arguments['--dry-run'] or None
    create_draft = arguments['--create-draft'] or None

    data_api_client = DataAPIClient(
        base_url=get_api_endpoint_from_stage(stage),
        auth_token=get_auth_token('api', stage)
    )
    content_loader = ContentLoader("../digitalmarketplace-frameworks")

    local_directory = arguments['--folder']

    # Check folder exists
    if local_directory and not os.path.exists(local_directory):
        print(f"Local directory {local_directory} not found. Aborting upload.")
        exit(1)

    # Check framework status
    framework = data_api_client.get_framework(framework_slug)
    framework_status = framework['frameworks']['status']
    if framework_status not in ['open', 'standstill']:
        print(f"Cannot update services for framework {framework_slug} in status '{framework_status}'")
        exit(1)

    update_draft_services_from_folder(
        local_directory,
        data_api_client,
        framework_slug,
        content_loader,
        dry_run,
        create_draft
    )
