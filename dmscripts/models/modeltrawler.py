import time
import itertools
import re
import collections


class ModelTrawler():

    def __init__(self, model, client):
        self.start = time.time()
        self.client = client
        self.model = model

        model_iter_method = "find_{}_iter".format(self.model)
        if not isinstance(getattr(self.client, model_iter_method, None), collections.Callable):
            raise AttributeError(
                "No model called '{}'. Allowed models are: {}".format(
                    self.model, list(self._get_allowed_models())
                )
            )

        self.model_iter_method = model_iter_method

    def _get_allowed_models(self):
        r = re.compile('^find_(\w*)_iter$')
        return (r.match(attr).group(1) for attr in dir(self.client) if r.match(attr))

    def _model_iter(self, **kwargs):
        for model in getattr(self.client, self.model_iter_method)(**kwargs):
            yield model

    def _filter_keys(self, _keys=None):

        def _get_nested_values(nested_keys, val):
            try:
                return val if not len(nested_keys) else _get_nested_values(nested_keys, val[nested_keys.pop(0)])
            except (KeyError, IndexError, TypeError):
                # objects/arrays might be empty for some returned models
                return ''

        def _filter_keys_inner(model_dict):
            """Takes a python dictionary and strips out non-specified keys

            --> IN -->
            _keys = (
                'id',
                ('user', 'emailAddress')
            )
            model_dict = {
                'id': 1,
                'name': 'Super cloud brief',
                'user': {'id': 101, 'emailAddress': 'user@gov.uk'}
            }

            <-- OUT <--
            {
                'id': 1,
                'emailAddress': 'user@gov.uk'
            }

            """

            if _keys is None:
                return model_dict

            filtered_dict = {}
            for key in _keys:
                if isinstance(key, (list, tuple)):
                    filtered_dict[".".join(str(k) for k in key)] = _get_nested_values(list(key), model_dict)
                else:
                    filtered_dict[key] = model_dict.get(key, '')

            return filtered_dict

        return _filter_keys_inner

    def get_data(self, keys=None, limit=None, **kwargs):
        models = self._model_iter(**kwargs)

        if limit is not None:
            models = itertools.islice(models, limit)

        return list(map(self._filter_keys(keys), models))

    def get_time_running(self):
        return time.time() - self.start
