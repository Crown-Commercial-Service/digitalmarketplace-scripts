import copy
import json
import logging
import lorem
import random
import re
import xeger
from jsonschema import validate, ValidationError

logger = logging.configure_logger()


class JsonSchemaDataFaker(object):

    """
    JSON Schema Data Faker takes a generated JSON schema and returns an object containing fake data that matches
    the constraints put forward by that schema.
    Only a subset of the JSON Schema syntax - enough to create fake G9 services - has been implemented.
    """

    def __init__(self, max_recalcs=100):
        """Instantiate the class.
        :param limit_calculations: Set the upper bounds on how many recalculations to run when generating data
            with max/min constraints, as this data is currently generated dumbly and then constrained afterwards."""
        self._max_recalcs = max_recalcs

    def _null(self, schema):
        return None

    def _boolean(self, schema):
        return random.choice([True, False])

    def _enum(self, schema):
        return random.choice(schema['enum'])

    def _array(self, schema):
        """Handles JSON Schema 'array' type: essentially a Python list"""
        min_items = schema.get('minItems', 1)
        max_items = schema.get('maxItems', 10)
        num_items = random.randint(min_items, max_items)

        if schema.get('uniqueItems', False):
            items = set()
            add_to_items = items.add
        else:
            items = []
            add_to_items = items.append

        attempts = 0
        while len(items) < num_items:
            len_items = len(items)

            add_to_items(self._parse_definition(schema['items']))

            # Prevent infinite loops
            if len_items == len(items):
                attempts += 1
                if attempts >= self._max_recalcs:
                    break
            else:
                attempts = 0

        return list(items)

    def _string(self, schema):
        """Handles JSON Schema 'string' type: essentially a Python str"""
        min_length = schema.get('minLength', 0)
        max_length = schema.get('maxLength', 100)

        random_string = lorem.text()[:random.randint(min_length, max_length)]

        if schema.get('pattern'):
            random_string = self._map_to_function('pattern')(random_string,
                                                             schema['pattern'],
                                                             min_length=min_length,
                                                             max_length=max_length)

        elif schema.get('format'):
            random_string = self._map_to_function(schema['format'])(min_length=min_length,
                                                                    max_length=max_length)

        return random_string

    def _pattern(self, current_string, pattern, min_length, max_length):
        """Generates a random string matching a given regex pattern, with min/max length constraints."""
        if re.match(pattern, current_string):
            return current_string

        random_string = ''
        attempts = 0

        while attempts < self._max_recalcs:
            random_string = xeger.xeger(pattern)

            if min_length < len(random_string) < max_length:
                return random_string

            attempts += 1

        logger.warning("Unable to generate within length constraints ({} < len < {}) for pattern: '{}'"
                       .format(min_length, max_length, pattern))

        return random_string

    def _uri(self, min_length, max_length):
        """Returns a random URL."""
        words = list(set(lorem.text().lower().replace('.', '').split()))

        scheme = random.choice(['http', 'https'])
        host = random.choice(words)
        tld = random.choice(['com', 'co.uk', 'gov.uk'])
        path = random.choice(words)

        return '{}://{}.{}/{}'.format(scheme, host, tld, path)

    def _map_to_function(self, name):
        """Utility function to map a JSON Schema type to the class function that handles it. This could be made more
        simple by not making the correlated functions protected, but I opted to do that in this instance as it feels
        more appropriate.

        e.g. 'enum'   -> def _enum
             'string' -> def _string"""
        return getattr(self, '_{}'.format(name))

    def _parse_definition(self, definition):
        if 'enum' in definition:
            return self._map_to_function('enum')(definition)

        return self._map_to_function(definition['type'])(definition)

    def _parse_schema(self, schema):
        generated_data = {}
        num_required = 0  # Start at 0 to kick-off while loop; tracks how many questions require answers
        properties = copy.deepcopy(schema["properties"])
        required_answers = set(schema["required"])

        # Until we have answers for all required questions, cycle through.
        while num_required < len(required_answers):
            num_required = len(required_answers)

            # Add answers for new required questions that don't have answers
            generated_data.update({prop: self._parse_definition(properties[prop])
                                   for prop in required_answers
                                   if prop not in generated_data})

            # Re-scan allOf validation, adding new required questions based on current answers
            for allof in schema['allOf']:
                for oneof in allof['oneOf']:
                    try:
                        for prop, definition in oneof['properties'].items():
                            validate(generated_data[prop] if prop in generated_data else None, definition)

                        logger.debug('[{}]: Validation succeeded.')

                    except ValidationError as e:
                        logger.debug('[{}]: Validation failed'.format(prop))

                    else:
                        if 'required' in oneof:
                            logger.debug('[{}]: Other questions required: {}'.format(prop, oneof['required']))

                            required_answers.update(oneof['required'])

        return generated_data

    def generate(self, root_schema):
        """Take a given JSON Schema and generate data matching the given constraints"""
        return self._parse_schema(root_schema)

    def generate_from_file(self, filepath):
        """Takes a filepath to a valid JSON Schema and generates data matching the given constraints."""
        with open(filepath) as infile:
            root_schema = json.loads(infile.read())

        return self.generate(root_schema)


class JsonSchemaGCloudServiceFaker(JsonSchemaDataFaker):
    def __init__(self, max_recalcs=100):
        super(self.__class__, self).__init__(max_recalcs)

    def _uri(self, min_length, max_length):
        return 'https://www.digitalmarketplace.service.gov.uk/uploaded_document.pdf'
