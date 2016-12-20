# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sys
if sys.version_info > (3, 0):
    import csv
else:
    import unicodecsv as csv

MANIFESTS = [{
    'question_set': 'declaration',
    'manifest':     'declaration'
    }, {
    'question_set': 'services',
    'manifest':     'edit_submission'
}]


def get_questions(questions):

    def augment_question_data(question, name, hint):
        question.multiquestion_name = name
        if hint:
            question.multiquestion_hint = hint
        return question

    def get_question(question):
        if question.questions:
            return [
                augment_question_data(nested_question, question.get('name'), question.get('hint'))
                for nested_question in question.questions
            ]

        return [question]

    questions_list = []
    for question in questions:
        questions_list += get_question(question)

    return questions_list


def return_rows_for_sections(sections):
    local_rows = []

    for section in sections:
        for question in get_questions(section.questions):
            row = [
                question.get('multiquestion_name', section.name),
                question.get('multiquestion_hint', None),
                question.get('question'),
                question.get('hint')
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


def generate_csv(output_directory, framework_slug, content_loader, context):

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    rows = []

    for manifest in MANIFESTS:
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

    with open('{}/{}-questions.csv'.format(output_directory, framework_slug), 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=b',', quotechar=b'"')
        header = ["Page title", "Page title hint", "Question", "Hint"]
        header.extend(
            ["Answer {}".format(i) for i in range(1, max_length_options+1)]
        )
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)
