# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sys
if sys.version_info > (3, 0):
    import csv
else:
    import unicodecsv as csv
import os.path

MANIFESTS = [{
    'question_set': 'declaration',
    'manifest':     'declaration'
    }, {
    'question_set': 'services',
    'manifest':     'edit_submission'
}]


def get_questions(questions):

    def augment_question_data(question, parent_question):
        question.parent = parent_question
        return question

    def get_question(question):
        # only multiquestions have nested (child) questions that we want to flatten into our CSV
        try:
            nested_questions = question.questions
        except AttributeError:
            return [question]

        return [
            augment_question_data(nested_question, question)
            for nested_question in nested_questions
        ]

    questions_list = []
    for question in questions:
        questions_list += get_question(question)

    return questions_list


def return_rows_for_sections(sections):
    local_rows = []

    for section in sections:
        for question in get_questions(section.questions):
            # Using get_source because we want the original markdown, not the rendered HTML
            # this means that no context can be reflected in the question content, i.e. our passed-in
            # context can only influence whether a question is displayed or not.
            # TODO if this turned out to matter, instead of get_source, we could convert back to markdown(!)

            parent = question.get('parent')
            page_title = parent.get_source('question') if parent else None
            section_and_page_title = ' / '.join([_f for _f in [section.name, page_title] if _f])

            # section.description is no longer expected to be used
            multiquestion_description = parent.get_source('description') if parent else None
            multiquestion_hint = parent.get_source('hint') if parent else None

            page_description = ' '.join([_f for _f in [multiquestion_description, multiquestion_hint] if _f])

            question_description = ' '.join([_f for _f in [
                question.get_source('description'),
                question.get_source('hint')
            ] if _f])

            row = [
                section_and_page_title,
                page_description,
                question.get_source('question'),
                question_description
            ]

            options = []
            for option in question.get('options', []):
                if 'label' in option:
                    options.append(option['label'])
                    if 'description' in option:
                        options[-1] = "{} - {}".format(options[-1], option['description'])

            if question.get('type') == 'boolean':
                options.append('Yes')
                options.append('No')
            row.extend(options)

            local_rows.append(row)

    # blank row
    local_rows.append([''] * 4)
    return local_rows


def generate_csv(output_file, framework_slug, content_loader, question_set, context):
    output_directory = os.path.dirname(output_file)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    rows = []

    for manifest in MANIFESTS:
        if not question_set or question_set == manifest['question_set']:
            content_loader.load_manifest(framework_slug, manifest['question_set'], manifest['manifest'])

            content = content_loader.get_manifest(framework_slug, manifest['manifest'])
            if context is not None:
                content = content.filter(context)

            rows.extend(return_rows_for_sections(content.sections))

    # find the longest array
    max_length = max(len(row) for row in rows)
    max_length_options = max_length - 4

    # push all arrays to that size
    for index, row in enumerate(rows):
        row.extend([''] * (max_length - len(row)))

    with open(output_file, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=b',', quotechar=b'"', quoting=csv.QUOTE_ALL)
        header = ["Section / page title", "Page description & hint", "Question", "Description & hint"]
        header.extend(
            ["Answer {}".format(i) for i in range(1, max_length_options+1)]
        )
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)
