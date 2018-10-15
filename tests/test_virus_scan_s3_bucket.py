from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
from itertools import groupby

import mock

import boto3
import pytest

from dmapiclient import AntivirusAPIClient

from dmscripts.virus_scan_s3_bucket import virus_scan_bucket


@contextmanager
def nullcontext():
    yield


class TestVirusScanBucket:
    # a sequence of pairs of (boto "Versions" entry, scan_and_tag_s3_object response) corresponding to each
    # "version" supposedly present in the bucket
    versions_responses = (
        (
            {
                "VersionId": "oo_.BepoodlLml",
                "Key": "sandman/4321-billy-winks.pdf",
                "LastModified": datetime(2012, 11, 10, 9, 8, 7),
            },
            {
                "existingAvStatus": {},
                "avStatusApplied": True,
                "newAvStatus": {"avStatus.result": "pass"},
            },
        ),
        (
            {
                "VersionId": "moB_eLplool.do",
                "Key": "sandman/4321-billy-winks.pdf",
                "LastModified": datetime(2012, 11, 10, 9, 8, 6),
            },
            {
                "existingAvStatus": {
                    "avStatus.result": "fail",
                    "avStatus.ts": "2013-12-11T10:11:12.76543Z",
                },
                "avStatusApplied": False,
                "newAvStatus": {"avStatus.result": "pass"},
            },
        ),
        (
            {
                "VersionId": "ooBmo_pe.ldoLl",
                "Key": "sandman/4321-billy-winks.pdf",
                "LastModified": datetime(2012, 11, 10, 9, 8, 8),
            },
            {
                "existingAvStatus": {},
                "avStatusApplied": True,
                "newAvStatus": {"avStatus.result": "fail"},
            },
        ),
        (
            {
                "VersionId": "epmlLoBodo_ol.",
                "Key": "sandman/1234-deedaw.pdf",
                "LastModified": datetime(2012, 11, 10, 9, 8, 5),
            },
            {
                "existingAvStatus": {},
                "avStatusApplied": True,
                "newAvStatus": {"avStatus.result": "pass"},
            },
        ),
        (
            {
                "VersionId": "loleLoooBp_md.",
                "Key": "sandman/1234-deedaw.pdf",
                "LastModified": datetime(2012, 11, 10, 9, 8, 4),
            },
            {
                "existingAvStatus": {"avStatus.irrelevant": "321"},
                "avStatusApplied": True,
                "newAvStatus": {"avStatus.result": "pass"},
            },
        ),
        (
            {
                "VersionId": "molo.oB_oLdelp",
                "Key": "sandman/4321-billy-winks.pdf",
                "LastModified": datetime(2012, 11, 10, 9, 8, 9),
            },
            {
                "existingAvStatus": {
                    "avStatus.result": "pass",
                    "avStatus.ts": "2013-12-11T10:09:08.76543Z",
                },
                "avStatusApplied": False,
                "newAvStatus": None,
            },
        ),
        (
            {
                "VersionId": "ldmoo_.pBeolLo",
                "Key": "dribbling/bib.jpeg",
                "LastModified": datetime(2012, 11, 10, 3, 0, 0),
            },
            {
                "existingAvStatus": {},
                "avStatusApplied": True,
                "newAvStatus": {"avStatus.result": "pass"},
            },
        ),
    )

    def _get_mock_clients(self, versions_responses, versions_page_size):
        # as nice as it would be to mock this at a higher level by using moto, at time of writing moto doesn't seem to
        # support the paging interface used by virus_scan_bucket

        # generate dict of responses for scan_and_tag_s3_object
        scan_tag_responses = {
            ("spade", version["Key"], version["VersionId"]): response
            for version, response in versions_responses
        }
        av_api_client = mock.create_autospec(AntivirusAPIClient)
        av_api_client.scan_and_tag_s3_object.side_effect = lambda b, k, v: scan_tag_responses[b, k, v]

        # generate sequence of "pages" to be returned by list_object_versions paginator, chunked by versions_page_size
        versions_pages = tuple(
            {
                "Versions": [version for i, (version, response) in versions_responses_chunk_iter],
                # ...omitting various other keys which would be present IRL...
            } for _, versions_responses_chunk_iter in groupby(
                enumerate(versions_responses),
                key=lambda i_vr: i_vr[0] // versions_page_size,
            )
        )
        s3_client = mock.create_autospec(boto3.client("s3"), instance=True)
        s3_client.get_paginator("").paginate.return_value = iter(versions_pages)
        s3_client.reset_mock()

        return av_api_client, s3_client

    @pytest.mark.parametrize("concurrency", (0, 1, 3,))
    @pytest.mark.parametrize("versions_page_size", (2, 4, 100,))
    @pytest.mark.parametrize("dry_run", (False, True,))
    def test_unfiltered(self, versions_page_size, dry_run, concurrency):
        av_api_client, s3_client = self._get_mock_clients(self.versions_responses, versions_page_size)

        with ThreadPoolExecutor(max_workers=concurrency) if concurrency else nullcontext() as executor:
            map_callable = map if executor is None else executor.map
            retval = virus_scan_bucket(
                s3_client,
                av_api_client,
                "spade",
                prefix="",
                since=None,
                dry_run=dry_run,
                map_callable=map_callable,
            )

        assert s3_client.mock_calls == [
            mock.call.get_paginator("list_object_versions"),
            mock.call.get_paginator().paginate(Bucket="spade", Prefix=""),
        ]

        if dry_run:
            assert av_api_client.mock_calls == []
            assert retval == (7, 0, 0, 0,)
        else:
            # taking string representations because call()s are not sortable and we want to disregard order
            assert sorted(str(c) for c in av_api_client.mock_calls) == sorted(str(c) for c in (
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "oo_.BepoodlLml"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "moB_eLplool.do"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "ooBmo_pe.ldoLl"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/1234-deedaw.pdf", "epmlLoBodo_ol."),
                mock.call.scan_and_tag_s3_object("spade", "sandman/1234-deedaw.pdf", "loleLoooBp_md."),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "molo.oB_oLdelp"),
                mock.call.scan_and_tag_s3_object("spade", "dribbling/bib.jpeg", "ldmoo_.pBeolLo"),
            ))
            assert retval == (7, 4, 1, 2,)

    @pytest.mark.parametrize("concurrency", (0, 1, 3,))
    @pytest.mark.parametrize("versions_page_size", (2, 4, 100,))
    @pytest.mark.parametrize("dry_run", (False, True,))
    def test_since_filtered(self, versions_page_size, dry_run, concurrency):
        av_api_client, s3_client = self._get_mock_clients(self.versions_responses, versions_page_size)

        with ThreadPoolExecutor(max_workers=concurrency) if concurrency else nullcontext() as executor:
            map_callable = map if executor is None else executor.map
            retval = virus_scan_bucket(
                s3_client,
                av_api_client,
                "spade",
                prefix="",
                since=datetime(2012, 11, 10, 9, 8, 7),
                dry_run=dry_run,
                map_callable=map_callable,
            )

        assert s3_client.mock_calls == [
            mock.call.get_paginator("list_object_versions"),
            mock.call.get_paginator().paginate(Bucket="spade", Prefix=""),
        ]

        if dry_run:
            assert av_api_client.mock_calls == []
            assert retval == (3, 0, 0, 0,)
        else:
            # taking string representations because call()s are not sortable and we want to disregard order
            assert sorted(str(c) for c in av_api_client.mock_calls) == sorted(str(c) for c in (
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "oo_.BepoodlLml"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "ooBmo_pe.ldoLl"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "molo.oB_oLdelp"),
            ))
            assert retval == (3, 1, 1, 1,)

    @pytest.mark.parametrize("concurrency", (0, 1, 3,))
    @pytest.mark.parametrize("versions_page_size", (2, 4, 100,))
    @pytest.mark.parametrize("dry_run", (False, True,))
    def test_prefix_filtered(self, versions_page_size, dry_run, concurrency):
        av_api_client, s3_client = self._get_mock_clients(
            tuple(v_r for v_r in self.versions_responses if v_r[0]["Key"].startswith("sand")),
            versions_page_size,
        )

        with ThreadPoolExecutor(max_workers=concurrency) if concurrency else nullcontext() as executor:
            map_callable = map if executor is None else executor.map
            retval = virus_scan_bucket(
                s3_client,
                av_api_client,
                "spade",
                prefix="sand",
                since=None,
                dry_run=dry_run,
                map_callable=map_callable,
            )

        assert s3_client.mock_calls == [
            mock.call.get_paginator("list_object_versions"),
            mock.call.get_paginator().paginate(Bucket="spade", Prefix="sand"),
        ]

        if dry_run:
            assert av_api_client.mock_calls == []
            assert retval == (6, 0, 0, 0,)
        else:
            # taking string representations because call()s are not sortable and we want to disregard order
            assert sorted(str(c) for c in av_api_client.mock_calls) == sorted(str(c) for c in (
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "oo_.BepoodlLml"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "moB_eLplool.do"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "ooBmo_pe.ldoLl"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/1234-deedaw.pdf", "epmlLoBodo_ol."),
                mock.call.scan_and_tag_s3_object("spade", "sandman/1234-deedaw.pdf", "loleLoooBp_md."),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "molo.oB_oLdelp"),
            ))
            assert retval == (6, 3, 1, 2,)
