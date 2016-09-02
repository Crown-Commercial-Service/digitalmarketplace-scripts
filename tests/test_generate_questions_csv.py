from dmcontent.content_loader import ContentSection
from dmscripts.generate_questions_csv import get_questions, return_rows_for_sections


def get_question(question_type, question_id):

    questions = {
        'text': {
            'question': 'Please type in an option',
            'type': 'text',
            'hint': 'Hint: please type in an option'
        },
        'boolean': {
            'question': 'Please confirm you can click options',
            'type': 'boolean',
        },
        'checkboxes': {
            'question': 'Which options can you click?',
            'type': 'checkboxes',
            'options': [
                {'label': 'Option 1', 'description': 'Description for option 1'},
                {'label': 'Option 2', 'description': 'Description for option 2'},
                {'label': 'Option 3', 'description': 'Description for option 3'}
            ]
        }
    }
    questions[question_type]['id'] = question_id
    return questions[question_type]


def get_section(questions=None, multiquestions=None):

    multiquestion = {
        'type': 'multiquestion',
        'questions': [],
        'question': 'Options',
        'name': 'Options',
        'id': 'options',
        'slug': 'options',
        'hint': 'Please indicate your preferred options'
    }

    section = {
        'editable': False,
        'description': None,
        'summary_page_description': 'You must be able to provide at least one option',
        'name': 'Options',
        'questions': [],
        'edit_questions': True,
        'id': 'options',
        'slug': 'options'
    }

    if questions is None:
        questions = []

    if multiquestions is None:
        multiquestions = []

    for index, question_type in enumerate(multiquestions):

        multiquestion['questions'].append(
            get_question(
                question_type,
                "multiquestion_{}".format(index)
            )
        )

    for index, question_type in enumerate(questions):

        section['questions'].append(
            get_question(
                question_type,
                "question_{}".format(index)
            ))

    if multiquestion['questions']:
        section['questions'].append(multiquestion)

    return section


def return_row_and_question(question_type, is_multiquestion=False):

    if is_multiquestion:
        section = ContentSection.create(section=get_section(
            multiquestions=[question_type],
        ))
    else:
        section = ContentSection.create(section=get_section(
            questions=[question_type],
        ))

    rows = return_rows_for_sections([section])
    question = get_question(question_type, '0')
    assert len(rows) == 2
    assert rows[0][0] == 'Options'
    assert rows[0][2] == question['question']
    if is_multiquestion:
        assert rows[0][1] == 'Please indicate your preferred options'

    return rows[0], question


def test_get_questions_unpacks_multiquestions():

    section = ContentSection.create(section=get_section(
        questions=['checkboxes', 'boolean'],
        multiquestions=['checkboxes', 'boolean']
    ))
    assert section.id == 'options'

    # should be a flat list with 4 entries
    questions = get_questions(section.questions)
    assert len(questions) == 4


def test_get_questions_sets_multiquestion_names_and_hints():

    section = ContentSection.create(section=get_section(
        multiquestions=['checkboxes', 'boolean']
    ))
    assert section.id == 'options'

    # hint and name of multiquestion should be preserved in nested_questions
    for question in get_questions(section.questions):
        if question.get('id').startswith('multiquestion_'):
            assert question.get('multiquestion_name') == 'Options'
            assert question.get('multiquestion_hint') == 'Please indicate your preferred options'


def test_return_row_for_text_question():

    question_row, question = return_row_and_question('text')
    multiquestion_row, question = return_row_and_question('text', is_multiquestion=True)

    for row in [question_row, multiquestion_row]:
        assert len(row) == 4
        assert row[3] == 'Hint: please type in an option'


def test_return_row_for_boolean_question():

    question_row, question = return_row_and_question('boolean')
    multiquestion_row, question = return_row_and_question('boolean', is_multiquestion=True)

    for row in [question_row, multiquestion_row]:
        assert len(row) == 6
        assert row[-2] == 'Yes'
        assert row[-1] == 'No'


def test_return_row_for_checkboxes_question():

    question_row, question = return_row_and_question('checkboxes')
    multiquestion_row, question = return_row_and_question('checkboxes', is_multiquestion=True)

    for row in [question_row, multiquestion_row]:
        assert (len(question_row) - 4) == len(question['options'])
        for index in range(len(question['options'])):
            assert question_row[index + 4] == "{} - {}".format(
                question['options'][index]['label'],
                question['options'][index]['description']
            )
