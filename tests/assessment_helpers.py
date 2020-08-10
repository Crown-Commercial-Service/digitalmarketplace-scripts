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
                    "allOf": [
                        {
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
                            "required": ["omnipresent"],
                        },
                    ],
                },
            },
        }

    def _get_ordered_question_ids(self):
        return (
            "shouldBeFalseLax",
            "shouldBeFalseStrict",
            "primaryContact",
            "primaryContactEmail",
            "shouldMatchPatternLax",
            "shouldMatchPatternStrict",
            "mitigatingFactors",
            "irrelevantQuestion",
            "mitigatingFactors2",
            "unmentionedQuestion",
            "mitigatingFactors3",
        )

    def _get_suppliers(self):
        return {
            supplier_id: {
                "id": supplier_id,
                "name": "Supplier {} generic name".format(supplier_id),
            }
            for supplier_id in self._get_supplier_frameworks().keys()
        }

    def _get_supplier_frameworks(self):
        return {
            k: dict(
                v,
                supplierId=k,
                frameworkSlug=self.framework_slug,
                countersignedPath="",
                countersignedAt="",
                declaration=dict(
                    v["declaration"],
                    primaryContact=u"Supplier {} Empl\u00f6yee 123".format(k),
                    primaryContactEmail="supplier.{}.{}@example.com".format(k, self.framework_slug),
                    mitigatingFactors=u"Permit, brevi manu, Supplier {}\u2019s sight is somewhat troubled".format(k),
                    mitigatingFactors2=(
                        u"Supplier {} can scarcely be prepared for every emergency that might crop up".format(k)
                    ),
                    mitigatingFactors3=(
                        u"Supplier {}'s dog ate their homework".format(k)
                    ),
                ),
            )
            for k, v in {
                # this has many fields filled out, the intention being to take a quick dict comprehension-modified copy
                # blanket-overriding any undesired values where necessary
                #
                # onFramework here is set to the expected result for the accompanying declaration, the idea being that
                # a subclass can override them with mismatched values if necessary
                1234: {
                    "onFramework": None,
                    "declaration": {
                        "status": "complete",
                        "shouldBeFalseLax": True,
                        "shouldBeTrueStrict": True,
                        "shouldMatchPatternStrict": "HE L Y   S",
                        "irrelevantQuestion": "Irrelevant answer",
                        "omnipresent": "ether",
                    },
                },
                2345: {
                    "onFramework": False,
                    "declaration": {
                        "status": "complete",
                        "shouldBeTrueLax": True,
                        "shouldMatchPatternLax": "Good pattern",
                        "shouldBeFalseStrict": None,  # <- subtle but important test here
                        "omnipresent": "ether",
                    },
                },
                3456: {
                    "onFramework": False,
                    "declaration": {
                        "status": "complete",
                        "omnipresent": "ether",
                    },
                },
                4321: {
                    "onFramework": True,
                    "declaration": {
                        "status": "complete",
                        "shouldBeTrueLax": True,
                        "shouldMatchPatternLax": "Good   Pattern",
                        "shouldMatchPatternStrict": "H.E. L.  Y",
                        "irrelevantStupidQuestion": "Irrelevant stupid answer",
                        "omnipresent": "ether",
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
                    "onFramework": False,
                    "declaration": {
                        "status": "complete",
                        "shouldBeFalseLax": True,
                        "shouldMatchPatternStrict": "HEL Y...",
                        "omnipresent": "ether",
                    },
                },
                7654: {
                    "onFramework": None,
                    "declaration": {
                        "status": "complete",
                        "shouldBeFalseLax": True,
                        "omnipresent": "ether",
                    },
                },
                8765: {
                    "onFramework": True,
                    "declaration": {
                        "status": "complete",
                        "shouldBeFalseLax": False,
                        "shouldBeTrueStrict": True,
                        "shouldMatchPatternLax": "Good    pattern",
                        "omnipresent": "ether",
                    },
                },
            }.items()
        }

    def _get_draft_services(self):
        return {
            s_id: tuple(dict(s, supplierId=s_id, frameworkSlug=self.framework_slug, lot=s["lotSlug"]) for s in v)
            for s_id, v in {
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
                7654: (
                    {
                        "id": 999011,
                        "status": "submitted",
                        "lotSlug": "pork-kidney",
                    },
                    {
                        "id": 999012,
                        "status": "not-submitted",
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
                        "status": "not-submitted",
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

    def _mock_get_supplier_framework_info_impl(self, supplier_id, framework_slug,):
        assert framework_slug == self.framework_slug
        return {
            "frameworkInterest": self.mock_supplier_frameworks[supplier_id],
        }

    def _mock_get_interested_suppliers_impl(self, framework_slug):
        assert framework_slug == self.framework_slug
        return {
            "interestedSuppliers": self.mock_supplier_frameworks.keys(),
        }

    def _mock_find_draft_services_iter_impl(self, supplier_id, framework=None):
        assert framework == self.framework_slug
        return iter(self.mock_draft_services[supplier_id])

    def _mock_get_supplier_impl(self, supplier_id):
        return {
            "suppliers": self.mock_suppliers[supplier_id]
        }

    def setup_method(self, method):
        self.mock_supplier_frameworks = self._get_supplier_frameworks()
        self.mock_draft_services = self._get_draft_services()
        self.mock_suppliers = self._get_suppliers()

        self.mock_data_client = Mock()
        self.mock_data_client.get_supplier_framework_info.side_effect = self._mock_get_supplier_framework_info_impl
        self.mock_data_client.get_interested_suppliers.side_effect = self._mock_get_interested_suppliers_impl
        self.mock_data_client.find_draft_services_iter.side_effect = self._mock_find_draft_services_iter_impl
        self.mock_data_client.get_supplier.side_effect = self._mock_get_supplier_impl


class _BaseAssessmentOverriddenOnFrameworksTestMixin(object):
    def _get_supplier_frameworks_overridden_on_framework_values(self):
        raise NotImplementedError

    def _get_supplier_frameworks(self):
        overridden_on_frameworks = self._get_supplier_frameworks_overridden_on_framework_values()
        # here we just override a bunch of the onFramework settings as desired by a subclass
        return {
            s_id: dict(sf, onFramework=overridden_on_frameworks.get(s_id, sf.get("onFramework")))
            for s_id, sf in super(
                _BaseAssessmentOverriddenOnFrameworksTestMixin,
                self,
            )._get_supplier_frameworks().items()
        }


class BaseAssessmentMismatchedOnFrameworksTestMixin(_BaseAssessmentOverriddenOnFrameworksTestMixin):
    def _get_supplier_frameworks_overridden_on_framework_values(self):
        # onFramework values that don't match the correct result for the associated declaration
        return {
            1234: True,
            2345: None,
            3456: True,
            4321: False,
            4567: False,
            5432: None,
            7654: None,
            8765: None,
        }


class BaseAssessmentOnFrameworksAsThoughNoBaselineTestMixin(_BaseAssessmentOverriddenOnFrameworksTestMixin):
    def _get_supplier_frameworks_overridden_on_framework_values(self):
        # onFramework values as though the baseline schema wasn't supplied
        return {
            1234: None,
            2345: None,
            3456: False,
            4321: True,
            4567: None,
            5432: None,
            7654: None,
            8765: True,
        }
