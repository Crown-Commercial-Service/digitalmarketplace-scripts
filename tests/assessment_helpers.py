from mock import Mock


class BaseAssessmentTest(object):
    framework_slug = "h-cloud-99"

    # putting these in methods so we are sure to always get a clean copy
    def _declaration_definite_pass_schema(self):
        return {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "allOf": [
                {"$ref": "#/definitions/baseline"},
                {
                    "properties": {
                        "shouldBeFalseLax": {"enum": [False]},
                        "shouldBeTrueLax": {"enum": [True]},
                        "shouldMatchPatternLax": {
                            "type": "string",
                            "pattern": "^Good +[Pp]attern",
                        },
                    },
                },
            ],
            "definitions": {
                "baseline": {
                    "$schema": "http://json-schema.org/draft-04/schema#",
                    "type": "object",
                    "properties": {
                        "shouldBeFalseStrict": {"enum": [False]},
                        "shouldBeTrueStrict": {"enum": [True]},
                        "shouldMatchPatternStrict": {
                            "type": "string",
                            "pattern": "^H\\.? *E\\.? *L\\.? *Y\\.? *S?",
                        },
                    },
                },
            },
        }

    # putting these in methods so we are sure to always get a clean copy
    def _draft_service_schema(self):
        return {
            "$schema": "http://json-schema.org/draft-04/schema#",
            "type": "object",
            "anyOf": [
                {
                    "properties": {
                        "lotSlug": {"enum": ["stuffed-roast-heart"]},
                        "kosher": {"type": "boolean"},
                    },
                    "required": ["kosher"],
                },
                {
                    "properties": {
                        "lotSlug": {"enum": ["pork-kidney", "ham-and-eggs"]},
                        "kosher": {"enum": [False]},
                        "butcher": {"enum": ["Dlugacz"]},
                    },
                },
                {
                    "properties": {
                        "lotSlug": {"enum": ["grilled-mutton-kidney"]},
                    },
                },
            ],
        }

    def _get_supplier_frameworks(self):
        return {k: dict(v, supplierId=k, frameworkSlug=self.framework_slug) for k, v in {
            # this has many fields filled out, the intention being to take a quick dict comprehension-modified copy blanket-
            # overriding any undesired values where necessary
            1234: {
                "onFramework": True,
                "declaration": {
                    "status": "complete",
                    "shouldBeFalseLax": True,
                    "shouldBeTrueStrict": True,
                    "shouldMatchPatternStrict": "HE L Y   S",
                    "irrelevantQuestion": "Irrelevant answer",
                },
            },
            2345: {
                "onFramework": None,
                "declaration": {
                    "status": "complete",
                    "shouldBeTrueLax": True,
                    "shouldMatchPatternLax": "Good pattern",
                    "shouldBeFalseStrict": None,  # <- subtle but important test here
                },
            },
            3456: {
                "onFramework": True,
                "declaration": {
                    "status": "complete",
                },
            },
            4321: {
                "onFramework": False,
                "declaration": {
                    "status": "complete",
                    "shouldBeTrueLax": True,
                    "shouldMatchPatternLax": "Good   Pattern",
                    "shouldMatchPatternStrict": "H.E. L.  Y",
                    "irrelevantStupidQuestion": "Irrelevant stupid answer",
                },
            },
            4567: {
                "onFramework": False,
                "declaration": {
                    "status": "bored-gave-up",
                    "shouldBeTrueStrict": True,
                },
            },
            5432: {
                "onFramework": None,
                "declaration": {
                    "status": "complete",
                    "shouldBeFalseLax": True,
                    "shouldMatchPatternStrict": "HEL Y...",
                },
            },
            6543: {
                "onFramework": None,
                "declaration": {
                    "status": "complete",
                    "shouldBeTrueStrict": True,
                },
            },
            7654: {
                "onFramework": None,
                "declaration": {
                    "status": "complete",
                    "shouldBeFalseLax": True,
                },
            },
            8765: {
                "onFramework": None,
                "declaration": {
                    "status": "complete",
                    "shouldBeFalseLax": False,
                    "shouldBeTrueStrict": True,
                    "shouldMatchPatternLax": "Good    pattern",
                },
            },
        }.items()}

    def _get_draft_services(self):
        return {
            s_id: tuple(dict(s, supplierId=s_id, frameworkSlug=self.framework_slug) for s in v) for s_id, v in {
                1234: (
                    {
                        "id": 999001,
                        "status": "submitted",
                        "lotSlug": "stuffed-roast-heart",
                        "kosher": False,
                    },
                ),
                2345: (
                    {
                        "id": 999002,
                        "status": "submitted",
                        "lotSlug": "ham-and-eggs",
                        "butcher": "Dlugacz",
                    },
                    {
                        "id": 999003,
                        "status": "submitted",
                        "lotSlug": "ham-and-eggs",
                        "kosher": True,
                    },
                    {
                        "id": 999004,
                        "status": "submitted",
                        "lotSlug": "pork-kidney",
                        "kosher": False,
                    },
                ),
                3456: (
                    {
                        "id": 999005,
                        "status": "submitted",
                        "lotSlug": "stuffed-roast-heart",
                    },
                ),
                4321: (
                    {
                        "id": 999006,
                        "status": "submitted",
                        "lotSlug": "grilled-mutton-kidney",
                        "butcher": "Buckley",
                    },
                    {
                        "id": 999007,
                        "status": "submitted",
                        "lotSlug": "pork-kidney",
                        "butcher": "Dlugacz",
                        "kosher": False,
                    },
                ),
                4567: (
                    {
                        "id": 999008,
                        "status": "not-submitted",
                        "lotSlug": "grilled-mutton-kidney",
                    },
                    {
                        "id": 999009,
                        "status": "submitted",
                        "lotSlug": "ham-and-eggs",
                        "anotherIrrelevantQuestion": "Another irrelevant answer",
                    },
                ),
                5432: (),
                6543: (
                    {
                        "id": 999010,
                        "status": "failed",
                        "lotSlug": "stuffed-roast-heart",
                        "kosher": True,
                    },
                ),
                7654: (
                    {
                        "id": 999011,
                        "status": "submitted",
                        "lotSlug": "pork-kidney",
                    },
                    {
                        "id": 999012,
                        "status": "failed",
                        "lotSlug": "stuffed-roast-heart",
                        "kosher": None,
                    },
                ),
                8765: (
                    {
                        "id": 999013,
                        "status": "submitted",
                        "lotSlug": "stuffed-roast-heart",
                        "kosher": False,
                    },
                    {
                        "id": 999014,
                        "status": "failed",
                        "lotSlug": "grilled-mutton-kidney",
                        "kosher": None,
                    },
                    {
                        "id": 999015,
                        "status": "submitted",
                        "lotSlug": "ham-and-eggs",
                        "butcher": "Dlugacz",
                        "kosher": False,
                    },
                    {
                        "id": 999016,
                        "status": "submitted",
                        "lotSlug": "stuffed-roast-heart",
                        "kosher": True,
                    },
                ),
            }.items()
        }

    def _mock_get_supplier_framework_info(self, supplier_id, framework_slug,):
        assert framework_slug == self.framework_slug
        return {
            "frameworkInterest": self.mock_supplier_frameworks[supplier_id],
        }

    def _mock_get_interested_suppliers(self, framework_slug):
        assert framework_slug == self.framework_slug
        return {
            "interestedSuppliers": self.mock_supplier_frameworks.keys(),
        }

    def _mock_find_draft_services_iter(self, supplier_id, framework=None):
        assert framework == self.framework_slug
        return iter(self.mock_draft_services[supplier_id])

    def setup_method(self, method):
        self.mock_supplier_frameworks = self._get_supplier_frameworks()
        self.mock_draft_services = self._get_draft_services()

        self.mock_data_client = Mock()
        self.mock_data_client.get_supplier_framework_info.side_effect = self._mock_get_supplier_framework_info
        self.mock_data_client.get_interested_suppliers.side_effect = self._mock_get_interested_suppliers
        self.mock_data_client.find_draft_services_iter.side_effect = self._mock_find_draft_services_iter
