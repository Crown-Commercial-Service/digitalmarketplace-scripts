from itertools import chain

import mock
import pytest

from dmapiclient import DataAPIClient, HTTPError
from dmtestutils.api_model_stubs import DraftServiceStub, ServiceStub, SupplierFrameworkStub
from dmtestutils.comparisons import ExactIdentity, AnyStringMatching
from dmtestutils.mocking import assert_args_and_return, assert_args_and_return_iter_over
from dmutils.s3 import S3

from dmscripts.publish_draft_services import (
    publish_draft_services, copy_draft_documents, publish_draft_service, get_draft_services_iter
)


@mock.patch('dmscripts.publish_draft_services.get_draft_services_iter')
@mock.patch('dmscripts.publish_draft_services.publish_draft_service')
@mock.patch('dmscripts.publish_draft_services.copy_draft_documents')
class TestPublishAndCopyDraftServices:

    def setup(self):
        self.mock_data_api_client = mock.create_autospec(DataAPIClient)
        self.draft_services_iter = []

        self.live_assets_endpoint = "https://boyish.gam/bols/"
        self.document_keys = ('123', '456')
        self.draft_service1 = DraftServiceStub(framework_slug="g-cloud-123", id=123).response()
        self.draft_service2 = DraftServiceStub(framework_slug="g-cloud-123", id=456).response()

    def find_draft_services_iter_side_effect(self, *args, **kwargs):
        return self.draft_service1, self.draft_service2

    @pytest.mark.parametrize("draft_ids_file", ("1, 2, 3", None))
    @pytest.mark.parametrize("dry_run", (False, True,))
    def test_publish_draft_services_happy_path(
        self, copy_draft_documents, publish_draft_service, get_draft_services_iter, dry_run, draft_ids_file
    ):
        get_draft_services_iter.side_effect = self.find_draft_services_iter_side_effect
        # Assume the drafts have not been previously published
        publish_draft_service.return_value = ("serviceID", False)

        publish_draft_services(
            self.mock_data_api_client,
            "g-cloud-123",
            'draft-bucket',
            'documents-bucket',
            self.document_keys,
            self.live_assets_endpoint,
            draft_ids_file=draft_ids_file,
            dry_run=dry_run,
        )

        assert publish_draft_service.mock_calls == [
            mock.call(
                self.mock_data_api_client,
                self.draft_service1,
                dry_run=dry_run,
            ),
            mock.call(
                self.mock_data_api_client,
                self.draft_service2,
                dry_run=dry_run,
            )
        ]
        assert copy_draft_documents.mock_calls == [
            mock.call(
                'draft-bucket',
                'documents-bucket',
                self.document_keys,
                self.live_assets_endpoint,
                self.mock_data_api_client,
                "g-cloud-123",
                self.draft_service1,
                "serviceID",
                dry_run
            ),
            mock.call(
                'draft-bucket',
                'documents-bucket',
                self.document_keys,
                self.live_assets_endpoint,
                self.mock_data_api_client,
                "g-cloud-123",
                self.draft_service2,
                "serviceID",
                dry_run
            ),
        ]
        assert get_draft_services_iter.mock_calls == [
            mock.call(
                self.mock_data_api_client,
                'g-cloud-123',
                draft_ids_file=draft_ids_file
            )
        ]

    @pytest.mark.parametrize("skip_docs_flag", (False, True,))
    @pytest.mark.parametrize("dry_run", (False, True,))
    def test_publish_draft_services_does_not_copy_if_copy_flag_false(
        self, copy_draft_documents, publish_draft_service, get_draft_services_iter, dry_run, skip_docs_flag
    ):
        get_draft_services_iter.side_effect = self.find_draft_services_iter_side_effect
        # Not yet published
        publish_draft_service.return_value = ("serviceID", False)

        publish_draft_services(
            self.mock_data_api_client,
            "g-cloud-123",
            'draft-bucket',
            'documents-bucket',
            self.document_keys,
            self.live_assets_endpoint,
            dry_run=dry_run,
            skip_docs_if_published=skip_docs_flag,
            copy_documents=False
        )
        assert len(copy_draft_documents.mock_calls) == 0

    @pytest.mark.parametrize("draft_ids_file", ("1, 2, 3", None))
    @pytest.mark.parametrize("dry_run", (False, True,))
    def test_publish_draft_services_skips_copying_if_draft_already_published(
        self, copy_draft_documents, publish_draft_service, get_draft_services_iter, dry_run, draft_ids_file
    ):
        get_draft_services_iter.side_effect = self.find_draft_services_iter_side_effect
        # Already published
        publish_draft_service.return_value = ("serviceID", True)

        publish_draft_services(
            self.mock_data_api_client,
            "g-cloud-123",
            'draft-bucket',
            'documents-bucket',
            self.document_keys,
            self.live_assets_endpoint,
            draft_ids_file=draft_ids_file,
            dry_run=dry_run,
        )
        assert len(copy_draft_documents.mock_calls) == 0

    @pytest.mark.parametrize("draft_ids_file", ("1, 2, 3", None))
    @pytest.mark.parametrize("dry_run", (False, True,))
    def test_publish_draft_services_does_not_skip_copying_published_docs_if_skip_flag_false(
        self, copy_draft_documents, publish_draft_service, get_draft_services_iter, dry_run, draft_ids_file
    ):
        get_draft_services_iter.side_effect = self.find_draft_services_iter_side_effect
        # Already published
        publish_draft_service.return_value = ("serviceID", True)

        publish_draft_services(
            self.mock_data_api_client,
            "g-cloud-123",
            'draft-bucket',
            'documents-bucket',
            self.document_keys,
            self.live_assets_endpoint,
            draft_ids_file=draft_ids_file,
            dry_run=dry_run,
            skip_docs_if_published=False,
        )
        assert len(copy_draft_documents.mock_calls) == 2


class TestGetDraftServicesIter:

    def setup(self):
        self.mock_data_api_client = mock.create_autospec(DataAPIClient)
        self.mock_data_api_client.find_framework_suppliers_iter.side_effect = assert_args_and_return_iter_over(
            (
                SupplierFrameworkStub(supplier_id=878004, framework_slug="g-cloud-123", on_framework=False).response(),
                SupplierFrameworkStub(supplier_id=878040, framework_slug="g-cloud-123", on_framework=True).response(),
                SupplierFrameworkStub(supplier_id=878400, framework_slug="g-cloud-123", on_framework=True).response(),
            ),
            "g-cloud-123",
            with_declarations=None
        )
        # 1: submitted, supplier not on framework
        # 2: not submitted, supplier on framework
        # 3 & 4: submitted, supplier on framework
        # 5: submitted, supplier on framework
        self.draft_service1 = DraftServiceStub(
            framework_slug="g-cloud-123", id=123, supplierId=878004, status='submitted'
        ).response()
        self.draft_service2 = DraftServiceStub(
            framework_slug="g-cloud-123", id=456, supplierId=878040, status='not-submitted'
        ).response()
        self.draft_service3 = DraftServiceStub(
            framework_slug="g-cloud-123", id=789, supplierId=878400, status='submitted'
        ).response()
        self.draft_service4 = DraftServiceStub(
            framework_slug="g-cloud-123", id=101, supplierId=878400, status='submitted'
        ).response()

        self.mock_data_api_client.find_draft_services_iter.side_effect = [
            [self.draft_service2],
            [self.draft_service3, self.draft_service4],
        ]

    def test_get_draft_services_fetches_drafts_for_framework_suppliers_only(self):
        drafts = get_draft_services_iter(self.mock_data_api_client, 'g-cloud-123')

        assert list(drafts) == [
            self.draft_service3,
            self.draft_service4,
        ]

    def test_get_draft_services_for_draft_ids_file_includes_not_submitted_services(self):
        self.mock_data_api_client.get_draft_service.side_effect = [
            {"services": self.draft_service2},
            {"services": self.draft_service3}
        ]
        draft_ids_file = """
            {0}
            {1}
            """.format(self.draft_service2['id'], self.draft_service3['id'])
        drafts = get_draft_services_iter(self.mock_data_api_client, 'g-cloud-123', draft_ids_file=draft_ids_file)

        assert list(drafts) == [
            self.draft_service2,
            self.draft_service3
        ]

    def test_get_draft_services_for_draft_ids_file_raises_on_supplier_id_mismatch(self):
        self.mock_data_api_client.get_draft_service.side_effect = [
            {"services": self.draft_service1}
        ]

        with pytest.raises(ValueError) as excinfo:
            list(get_draft_services_iter(self.mock_data_api_client, 'g-cloud-123', draft_ids_file="1"))

        assert str(excinfo.value) == "Draft service 1's supplier (878004) not on framework 'g-cloud-123'"


@pytest.mark.parametrize("dry_run", (False, True,))
@pytest.mark.parametrize("skip_docs_if_published", (False, True,))
@mock.patch('dmscripts.publish_draft_services.copy_draft_documents')
def test_publish_draft_services(copy_draft_documents, skip_docs_if_published, dry_run):
    draft_service_kwargs_by_supplier = {
        supplier_id: tuple(
            {
                "supplier_id": supplier_id,
                "framework_slug": "g-cloud-123",
                **ds_kwargs,
            }
            for ds_kwargs in ds_kwargs_seq
        )
        for supplier_id, ds_kwargs_seq in {
            878004: (
                {"id": 494003, "status": "submitted"},
            ),
            878040: (
                {"id": 495002, "status": "not-submitted"},
                {"id": 495102, "status": "submitted"},
                {"id": 495012, "status": "submitted"},
            ),
            878400: (
                {"id": 493001, "status": "not-submitted"},
            ),
            878005: (
                {"id": 492004, "status": "submitted"},
                {"id": 492044, "status": "submitted", "serviceId": "4448882220"},
                {"id": 492444, "status": "submitted"},
            ),
            878050: (
                {"id": 496003, "status": "submitted"},
            ),
            878500: (
                {"id": 497005, "status": "submitted"},
            ),
        }.items()
    }
    draft_service_kwargs_by_id = {
        draft_service_kwargs["id"]: draft_service_kwargs
        for draft_service_kwargs in chain.from_iterable(draft_service_kwargs_by_supplier.values())
    }

    mock_data_api_client = mock.create_autospec(DataAPIClient)
    mock_data_api_client.find_framework_suppliers_iter.side_effect = assert_args_and_return_iter_over(
        (
            SupplierFrameworkStub(supplier_id=878004, framework_slug="g-cloud-123", on_framework=False).response(),
            SupplierFrameworkStub(supplier_id=878040, framework_slug="g-cloud-123", on_framework=True).response(),
            SupplierFrameworkStub(supplier_id=878400, framework_slug="g-cloud-123", on_framework=True).response(),
            SupplierFrameworkStub(supplier_id=878005, framework_slug="g-cloud-123", on_framework=True).response(),
            SupplierFrameworkStub(supplier_id=878050, framework_slug="g-cloud-123", on_framework=False).response(),
            SupplierFrameworkStub(supplier_id=878500, framework_slug="g-cloud-123", on_framework=True).response(),
        ),
        "g-cloud-123",
        with_declarations=None,
    )

    def find_draft_services_iter_side_effect(supplier_id, **kwargs):
        assert kwargs["framework"] == "g-cloud-123"
        return (DraftServiceStub(**dsk).response() for dsk in draft_service_kwargs_by_supplier[supplier_id])
    mock_data_api_client.find_draft_services_iter.side_effect = find_draft_services_iter_side_effect

    def publish_draft_service_side_effect(draft_id, user):
        if draft_id == 495012:
            # simulate the draft somehow being published by something else after we originally fetched & checked it
            mock_response = mock.Mock(status_code=400)
            mock_response.json.return_value = {"error": "Cannot re-publish a submitted service"}
            raise HTTPError(response=mock_response)

        draft_rd = DraftServiceStub(**draft_service_kwargs_by_id[draft_id]).response()
        return ServiceStub(
            service_id=str(draft_id).rjust(10, "7"),
            **{k: draft_rd[k] for k in ("supplierId", "frameworkSlug", "lot",)}
        ).single_result_response()
    mock_data_api_client.publish_draft_service.side_effect = publish_draft_service_side_effect

    # this should only ever be called once the script realizes 495012 has been published and wants to find out its
    # assigned service id
    mock_data_api_client.get_draft_service.side_effect = assert_args_and_return(
        DraftServiceStub(**draft_service_kwargs_by_id[495012], serviceId="1112223334").response(),
        495012,
    )

    publish_draft_services(
        mock_data_api_client,
        "g-cloud-123",
        'draft-bucket',
        'documents-bucket',
        ('123', '456'),
        'https://boyish.gam/bols/',
        draft_ids_file=None,
        dry_run=dry_run,
        skip_docs_if_published=skip_docs_if_published,
        copy_documents=True
    )

    assert mock_data_api_client.find_framework_suppliers_iter.called is True

    assert mock_data_api_client.find_draft_services_iter.mock_calls == [
        mock.call(878040, framework="g-cloud-123"),
        mock.call(878400, framework="g-cloud-123"),
        mock.call(878005, framework="g-cloud-123"),
        mock.call(878500, framework="g-cloud-123"),
    ]

    # shouldn't get called at all in the dry_run_case
    assert mock_data_api_client.publish_draft_service.mock_calls == [] if dry_run else [
        mock.call(495102, "publish_draft_services.py"),
        mock.call(495012, "publish_draft_services.py"),
        mock.call(492004, "publish_draft_services.py"),
        mock.call(492444, "publish_draft_services.py"),
        mock.call(497005, "publish_draft_services.py"),
    ]

    # would only be called as a result of a publish_draft_service call going wrong
    assert mock_data_api_client.get_draft_service.called is (not dry_run)

    assert copy_draft_documents.mock_calls == [
        x for x in (
            mock.call(
                'draft-bucket',
                'documents-bucket',
                ('123', '456'),
                'https://boyish.gam/bols/',
                ExactIdentity(mock_data_api_client),
                "g-cloud-123",
                DraftServiceStub(**draft_service_kwargs_by_id[495102]).response(),
                AnyStringMatching(r"555.*") if dry_run else "7777495102",
                dry_run
            ),
            mock.call(
                'draft-bucket',
                'documents-bucket',
                ('123', '456'),
                'https://boyish.gam/bols/',
                ExactIdentity(mock_data_api_client),
                "g-cloud-123",
                DraftServiceStub(
                    **draft_service_kwargs_by_id[495012],
                ).response(),
                # if it's a dry_run, then the script never discovers its already-assigned id 1112223334
                AnyStringMatching(r"555.*") if dry_run else "1112223334",
                dry_run
                # if it's a dry_run then the script never discovers that it's already published so will call
                # either way
            ) if dry_run or not skip_docs_if_published else None,
            mock.call(
                'draft-bucket',
                'documents-bucket',
                ('123', '456'),
                'https://boyish.gam/bols/',
                ExactIdentity(mock_data_api_client),
                "g-cloud-123",
                DraftServiceStub(**draft_service_kwargs_by_id[492004]).response(),
                AnyStringMatching(r"555.*") if dry_run else "7777492004",
                dry_run
            ),
            mock.call(
                'draft-bucket',
                'documents-bucket',
                ('123', '456'),
                'https://boyish.gam/bols/',
                ExactIdentity(mock_data_api_client),
                "g-cloud-123",
                DraftServiceStub(**draft_service_kwargs_by_id[492044]).response(),
                "4448882220",
                dry_run
            ) if not skip_docs_if_published else None,
            mock.call(
                'draft-bucket',
                'documents-bucket',
                ('123', '456'),
                'https://boyish.gam/bols/',
                ExactIdentity(mock_data_api_client),
                "g-cloud-123",
                DraftServiceStub(**draft_service_kwargs_by_id[492444]).response(),
                AnyStringMatching(r"555.*") if dry_run else "7777492444",
                dry_run
            ),
            mock.call(
                'draft-bucket',
                'documents-bucket',
                ('123', '456'),
                'https://boyish.gam/bols/',
                ExactIdentity(mock_data_api_client),
                "g-cloud-123",
                DraftServiceStub(**draft_service_kwargs_by_id[497005]).response(),
                AnyStringMatching(r"555.*") if dry_run else "7777497005",
                dry_run
            ),
        ) if x is not None
    ]


class TestPublishDraftService:

    def setup(self):
        self.mock_data_api_client = mock.create_autospec(DataAPIClient)
        self.mock_data_api_client.publish_draft_service.return_value = {
            "services": {
                "id": "500400300"
            }
        }
        self.mock_data_api_client.get_draft_service.return_value = {
            "serviceId": "500400200",
            "supplierId": 999,
            "id": 987654
        }

        self.draft_service = {
            "supplierId": 999,
            "id": 987654
        }

    @pytest.mark.parametrize("dry_run", (False, True,))
    @mock.patch('dmscripts.publish_draft_services.get_logger')
    def test_publish_draft_service_with_service_id_logs_warning(self, logger_mock, dry_run):
        draft_service_with_existing_id = {
            "serviceId": "12345678",
            "supplierId": 999,
            "id": 987654
        }
        assert publish_draft_service(
            self.mock_data_api_client,
            draft_service_with_existing_id
        ) == ("12345678", True)

        assert logger_mock.return_value.info.call_args_list == [
            mock.call("supplier %s: draft %s: publishing", 999, 987654)
        ]
        assert logger_mock.return_value.warning.call_args_list == [
            mock.call(
                "supplier %s: draft %s: skipped publishing - already has service id: %s",
                999,
                987654,
                "12345678"
            )
        ]

    @mock.patch('dmscripts.publish_draft_services.random')
    @mock.patch('dmscripts.publish_draft_services.get_logger')
    def test_publish_draft_service_with_dry_run_only_logs(self, logger_mock, random):
        random.randint.return_value = "55500001"

        assert publish_draft_service(
            self.mock_data_api_client,
            self.draft_service,
            dry_run=True,
        ) == ("55500001", False)

        assert logger_mock.return_value.info.call_args_list == [
            mock.call("supplier %s: draft %s: publishing", 999, 987654),
            mock.call(
                "supplier %s: draft %s: dry run: generating random test service id: %s",
                999,
                987654,
                "55500001"
            )
        ]

    @mock.patch('dmscripts.publish_draft_services.get_logger')
    def test_publish_draft_service_happy_path(self, logger_mock):

        assert publish_draft_service(
            self.mock_data_api_client,
            self.draft_service,
            dry_run=False,
        ) == ("500400300", False)

        assert self.mock_data_api_client.publish_draft_service.call_args_list == [
            mock.call(987654, user='publish_draft_services.py')
        ]
        assert self.mock_data_api_client.get_draft_service.call_args_list == []
        assert logger_mock.return_value.info.call_args_list == [
            mock.call("supplier %s: draft %s: publishing", 999, 987654),
            mock.call(
                "supplier %s: draft %s: published - new service id: %s",
                999,
                987654,
                "500400300"
            )
        ]

    @mock.patch('dmscripts.publish_draft_services.get_logger')
    def test_publish_draft_service_retries_republish_api_error(self, logger_mock):
        mock_response = mock.Mock(status_code=400)
        mock_response.json.return_value = {"error": "Cannot re-publish a submitted service"}
        self.mock_data_api_client.publish_draft_service.side_effect = HTTPError(
            response=mock_response
        )

        assert publish_draft_service(
            self.mock_data_api_client,
            self.draft_service,
            dry_run=False,
        ) == ("500400200", True)

        assert self.mock_data_api_client.publish_draft_service.call_args_list == [
            mock.call(987654, user='publish_draft_services.py')
        ]
        assert self.mock_data_api_client.get_draft_service.call_args_list == [
            mock.call(987654)
        ]
        assert logger_mock.return_value.info.call_args_list == [
            mock.call("supplier %s: draft %s: publishing", 999, 987654)
        ]
        assert logger_mock.return_value.warning.call_args_list == [
            mock.call(
                "supplier %s: draft %s: failed publishing - has service id: %s",
                999,
                987654,
                "500400200",
            )
        ]


class TestCopyDraftDocuments:

    def setup(self):
        self.mock_draft_bucket = mock.create_autospec(S3, bucket_name="ducky")
        self.mock_draft_bucket.path_exists.return_value = True
        self.mock_documents_bucket = mock.create_autospec(S3, bucket_name="puddeny-pie")
        self.mock_data_api_client = mock.create_autospec(DataAPIClient)

        self.draft_service = DraftServiceStub(
            id=379001,
            framework_slug="g-cloud-123",
            supplier_id="171400",
            service_id="2229090909",
            **{
                "chinChopperURL": "https://gin.ger.br/ead/g-cloud-123/submissions/171400/379001-steak.pdf",
                "beeoTeeTomURL": "https://gin.ger.br/ead/g-cloud-123/submissions/171400/379001-kidney.pdf",
                "madcapURL": "https://gin.ger.br/ead/g-cloud-123/submissions/171400/379001-liver.odt",
                "boldAsBrassURL": "https://gin.ger.br/ead/g-cloud-123/submissions/171400/379001-mashed.pdf",
            }
        ).response()
        self.document_keys = (
            "chinChopperURL",
            "beeoTeeTomURL",
            "madcapURL",
            "boldAsBrassURL",
        )
        self.live_assets_endpoint = "https://boyish.gam/bols/"

    def mock_documents_bucket_copy_side_effect(self, src_bucket, src_key, target_key, **kwargs):
        # Raise an error if this document already exists in the target bucket
        if target_key == "g-cloud-123/documents/171400/2229090909-kidney.pdf":
            raise ValueError("Target key already exists in S3.")
        return mock.Mock()

    def test_copy_draft_documents_only_logs_on_dry_run(self):
        copy_draft_documents(
            self.mock_draft_bucket,
            self.mock_documents_bucket,
            self.document_keys,
            self.live_assets_endpoint,
            self.mock_data_api_client,
            "g-cloud-123",
            self.draft_service,
            "2229090909",
        )

        assert self.mock_draft_bucket.mock_calls == [
            mock.call.path_exists("g-cloud-123/submissions/171400/379001-steak.pdf"),
            mock.call.path_exists("g-cloud-123/submissions/171400/379001-kidney.pdf"),
            mock.call.path_exists("g-cloud-123/submissions/171400/379001-liver.odt"),
            mock.call.path_exists("g-cloud-123/submissions/171400/379001-mashed.pdf"),
        ]

        assert self.mock_documents_bucket.mock_calls == []
        assert self.mock_data_api_client.mock_calls == []

    def test_copy_draft_documents_happy_path(self):
        copy_draft_documents(
            self.mock_draft_bucket,
            self.mock_documents_bucket,
            self.document_keys,
            self.live_assets_endpoint,
            self.mock_data_api_client,
            "g-cloud-123",
            self.draft_service,
            "2229090909",
            dry_run=False,
        )

        assert self.mock_draft_bucket.mock_calls == [
            mock.call.path_exists("g-cloud-123/submissions/171400/379001-steak.pdf"),
            mock.call.path_exists("g-cloud-123/submissions/171400/379001-kidney.pdf"),
            mock.call.path_exists("g-cloud-123/submissions/171400/379001-liver.odt"),
            mock.call.path_exists("g-cloud-123/submissions/171400/379001-mashed.pdf"),
        ]

        assert self.mock_documents_bucket.mock_calls == [
            mock.call.copy(
                acl="public-read",
                src_bucket="ducky",
                src_key="g-cloud-123/submissions/171400/379001-steak.pdf",
                target_key="g-cloud-123/documents/171400/2229090909-steak.pdf",
            ),
            mock.call.copy(
                acl="public-read",
                src_bucket="ducky",
                src_key="g-cloud-123/submissions/171400/379001-kidney.pdf",
                target_key="g-cloud-123/documents/171400/2229090909-kidney.pdf",
            ),
            mock.call.copy(
                acl="public-read",
                src_bucket="ducky",
                src_key="g-cloud-123/submissions/171400/379001-liver.odt",
                target_key="g-cloud-123/documents/171400/2229090909-liver.odt",
            ),
            mock.call.copy(
                acl="public-read",
                src_bucket="ducky",
                src_key="g-cloud-123/submissions/171400/379001-mashed.pdf",
                target_key="g-cloud-123/documents/171400/2229090909-mashed.pdf",
            ),
        ]

        assert self.mock_data_api_client.mock_calls == [
            mock.call.update_service(
                "2229090909",
                {
                    "chinChopperURL": "https://boyish.gam/bols/g-cloud-123/documents/171400/2229090909-steak.pdf",
                    "beeoTeeTomURL": "https://boyish.gam/bols/g-cloud-123/documents/171400/2229090909-kidney.pdf",
                    "madcapURL": "https://boyish.gam/bols/g-cloud-123/documents/171400/2229090909-liver.odt",
                    "boldAsBrassURL": "https://boyish.gam/bols/g-cloud-123/documents/171400/2229090909-mashed.pdf",
                },
                user="publish_draft_services.py",
            ),
        ]

    def test_copy_draft_documents_raises_on_supplier_id_mismatch(self):
        draft_service_with_bad_document_path = DraftServiceStub(
            id=379001,
            framework_slug="g-cloud-123",
            supplier_id="171400",
            service_id="2229090909",
            **{
                "chinChopperURL": "https://gin.ger.br/ead/g-cloud-123/submissions/999999/379001-steak.pdf",
                "beeoTeeTomURL": "https://gin.ger.br/ead/g-cloud-123/submissions/171400/379001-kidney.pdf",
            }
        ).response()

        with pytest.raises(ValueError) as excinfo:
            copy_draft_documents(
                self.mock_draft_bucket,
                self.mock_documents_bucket,
                self.document_keys,
                self.live_assets_endpoint,
                self.mock_data_api_client,
                "g-cloud-123",
                draft_service_with_bad_document_path,
                "2229090909",
                dry_run=False,
            )

        assert str(excinfo.value) == "supplier id mismatch: '999999' != '171400'"
        assert self.mock_documents_bucket.mock_calls == []
        assert self.mock_data_api_client.mock_calls == []

    def test_copy_draft_documents_raises_on_draft_service_id_mismatch(self):
        draft_service_with_bad_document_path = DraftServiceStub(
            id=379001,
            framework_slug="g-cloud-123",
            supplier_id="171400",
            service_id="2229090909",
            **{
                "chinChopperURL": "https://gin.ger.br/ead/g-cloud-123/submissions/171400/999999-steak.pdf",
                "beeoTeeTomURL": "https://gin.ger.br/ead/g-cloud-123/submissions/171400/379001-kidney.pdf",
            }
        ).response()

        with pytest.raises(ValueError) as excinfo:
            copy_draft_documents(
                self.mock_draft_bucket,
                self.mock_documents_bucket,
                self.document_keys,
                self.live_assets_endpoint,
                self.mock_data_api_client,
                "g-cloud-123",
                draft_service_with_bad_document_path,
                "2229090909",
                dry_run=False,
            )

        assert str(excinfo.value) == "draft id mismatch: '999999' != '379001'"
        assert self.mock_documents_bucket.mock_calls == []
        assert self.mock_data_api_client.mock_calls == []

    def test_copy_draft_documents_ignores_error_if_document_exists_in_target_bucket(self):
        self.mock_documents_bucket.copy.side_effect = self.mock_documents_bucket_copy_side_effect

        copy_draft_documents(
            self.mock_draft_bucket,
            self.mock_documents_bucket,
            self.document_keys,
            self.live_assets_endpoint,
            self.mock_data_api_client,
            "g-cloud-123",
            self.draft_service,
            "2229090909",
            dry_run=False,
        )
        # Service is updated as normal
        assert self.mock_data_api_client.mock_calls == [
            mock.call.update_service(
                "2229090909",
                {
                    "chinChopperURL": "https://boyish.gam/bols/g-cloud-123/documents/171400/2229090909-steak.pdf",
                    "beeoTeeTomURL": "https://boyish.gam/bols/g-cloud-123/documents/171400/2229090909-kidney.pdf",
                    "madcapURL": "https://boyish.gam/bols/g-cloud-123/documents/171400/2229090909-liver.odt",
                    "boldAsBrassURL": "https://boyish.gam/bols/g-cloud-123/documents/171400/2229090909-mashed.pdf",
                },
                user="publish_draft_services.py",
            ),
        ]

    def test_copy_draft_documents_raises_on_other_copy_error(self):
        self.mock_documents_bucket.copy.side_effect = ValueError("Unexpected S3 error.")
        with pytest.raises(ValueError) as excinfo:
            copy_draft_documents(
                self.mock_draft_bucket,
                self.mock_documents_bucket,
                self.document_keys,
                self.live_assets_endpoint,
                self.mock_data_api_client,
                "g-cloud-123",
                self.draft_service,
                "2229090909",
                dry_run=False,
            )

        assert str(excinfo.value) == "Unexpected S3 error."
