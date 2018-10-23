from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
from itertools import chain, groupby

import mock

import boto3
import pytest

from dmapiclient import AntivirusAPIClient
from dmapiclient.errors import APIError

from dmscripts.virus_scan_s3_bucket import virus_scan_bucket


@contextmanager
def nullcontext():
    yield


def _raise_if_exc(maybe_exception):
    if isinstance(maybe_exception, Exception):
        raise maybe_exception
    return maybe_exception


@pytest.mark.parametrize("concurrency", (0, 1, 3,))
@pytest.mark.parametrize("versions_page_size", (2, 4, 100,))
@pytest.mark.parametrize("dry_run", (False, True,))
class TestVirusScanBucket:
    # a dict of sequences of pairs of (boto "Versions" entry, scan_and_tag_s3_object response) corresponding to each
    # "version" supposedly present in each bucket named by the top-level dict key
    buckets_versions_responses = {
        "spade": (
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
        ),
        "martello": (
            (
                {
                    "VersionId": "lFHrwenroye_",
                    "Key": "unmentionables.PNG",
                    "LastModified": datetime(2012, 12, 11, 10, 9, 8),
                },
                {
                    "existingAvStatus": {},
                    "avStatusApplied": True,
                    "newAvStatus": {"avStatus.result": "fail"},
                },
            ),
            (
                {
                    "VersionId": "nHwr_elFoyre",
                    "Key": "sandy/mount.pdf",
                    "LastModified": datetime(2012, 12, 9, 22, 23, 24),
                },
                {
                    "existingAvStatus": {
                        "avStatus.result": "pass",
                        "avStatus.ts": "2013-12-10T11:08:09.67534Z",
                    },
                    "avStatusApplied": False,
                    "newAvStatus": {"avStatus.result": "fail"},
                },
            ),
            (
                {
                    "VersionId": "Hn_olFerweyr",
                    "Key": "handy/mount.pdf",
                    "LastModified": datetime(2012, 12, 9, 23, 24, 25),
                },
                APIError(response=mock.Mock(status_code=403), message="Forbidden"),
            ),
        ),
    }

    def _get_mock_clients(self, buckets_versions_responses, versions_page_size):
        # as nice as it would be to mock this at a higher level by using moto, at time of writing moto doesn't seem to
        # support the paging interface used by virus_scan_bucket

        # generate dict of responses for scan_and_tag_s3_object
        scan_tag_responses = {
            (bucket_name, version["Key"], version["VersionId"]): response
            for bucket_name, version, response in chain.from_iterable(
                ((bucket_name, *v_r) for v_r in v_rs)
                for bucket_name, v_rs in buckets_versions_responses.items()
            )
        }
        av_api_client = mock.create_autospec(AntivirusAPIClient)
        av_api_client.scan_and_tag_s3_object.side_effect = lambda b, k, v: _raise_if_exc(scan_tag_responses[b, k, v])

        # generate sequence of "pages" to be returned by list_object_versions paginator, chunked by versions_page_size
        versions_pages = {
            bucket_name: tuple(
                {
                    "Versions": [version for i, (version, response) in versions_responses_chunk_iter],
                    # ...omitting various other keys which would be present IRL...
                } for _, versions_responses_chunk_iter in groupby(
                    enumerate(versions_responses),
                    key=lambda i_vr: i_vr[0] // versions_page_size,
                )
            ) for bucket_name, versions_responses in buckets_versions_responses.items()
        }
        s3_client = mock.create_autospec(boto3.client("s3"), instance=True)
        s3_client.get_paginator("").paginate.side_effect = lambda *args, Bucket, **kwargs: iter(versions_pages[Bucket])
        s3_client.reset_mock()

        return av_api_client, s3_client

    def test_unfiltered_single_bucket(self, versions_page_size, dry_run, concurrency):
        av_api_client, s3_client = self._get_mock_clients(self.buckets_versions_responses, versions_page_size)

        with ThreadPoolExecutor(max_workers=concurrency) if concurrency else nullcontext() as executor:
            map_callable = map if executor is None else executor.map
            retval = virus_scan_bucket(
                s3_client,
                av_api_client,
                ("spade",),
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
            assert retval == Counter({"candidate": 7})
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
            assert retval == Counter({
                "candidate": 7,
                "pass": 4,
                "fail": 1,
                "already_tagged": 2,
            })

    def test_unfiltered_multi_bucket(self, versions_page_size, dry_run, concurrency):
        av_api_client, s3_client = self._get_mock_clients(self.buckets_versions_responses, versions_page_size)

        with ThreadPoolExecutor(max_workers=concurrency) if concurrency else nullcontext() as executor:
            map_callable = map if executor is None else executor.map
            retval = virus_scan_bucket(
                s3_client,
                av_api_client,
                ("spade", "martello",),
                prefix="",
                since=None,
                dry_run=dry_run,
                map_callable=map_callable,
            )

        assert s3_client.mock_calls == [
            mock.call.get_paginator("list_object_versions"),
            mock.call.get_paginator().paginate(Bucket="spade", Prefix=""),
            mock.call.get_paginator("list_object_versions"),
            mock.call.get_paginator().paginate(Bucket="martello", Prefix=""),
        ]

        if dry_run:
            assert av_api_client.mock_calls == []
            assert retval == Counter({"candidate": 10})
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
                mock.call.scan_and_tag_s3_object("martello", "unmentionables.PNG", "lFHrwenroye_"),
                mock.call.scan_and_tag_s3_object("martello", "sandy/mount.pdf", "nHwr_elFoyre"),
                mock.call.scan_and_tag_s3_object("martello", "handy/mount.pdf", "Hn_olFerweyr"),
            ))
            assert retval == Counter({
                "candidate": 10,
                "pass": 4,
                "fail": 2,
                "already_tagged": 3,
                "error": 1,
            })

    def test_since_filtered_single_bucket(self, versions_page_size, dry_run, concurrency):
        av_api_client, s3_client = self._get_mock_clients(self.buckets_versions_responses, versions_page_size)

        with ThreadPoolExecutor(max_workers=concurrency) if concurrency else nullcontext() as executor:
            map_callable = map if executor is None else executor.map
            retval = virus_scan_bucket(
                s3_client,
                av_api_client,
                ("spade",),
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
            assert retval == Counter({"candidate": 3})
        else:
            # taking string representations because call()s are not sortable and we want to disregard order
            assert sorted(str(c) for c in av_api_client.mock_calls) == sorted(str(c) for c in (
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "oo_.BepoodlLml"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "ooBmo_pe.ldoLl"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "molo.oB_oLdelp"),
            ))
            assert retval == Counter({
                "candidate": 3,
                "pass": 1,
                "fail": 1,
                "already_tagged": 1,
            })

    def test_since_filtered_multi_bucket(self, versions_page_size, dry_run, concurrency):
        av_api_client, s3_client = self._get_mock_clients(self.buckets_versions_responses, versions_page_size)

        with ThreadPoolExecutor(max_workers=concurrency) if concurrency else nullcontext() as executor:
            map_callable = map if executor is None else executor.map
            retval = virus_scan_bucket(
                s3_client,
                av_api_client,
                ("spade", "martello",),
                prefix="",
                since=datetime(2012, 11, 10, 9, 8, 7),
                dry_run=dry_run,
                map_callable=map_callable,
            )

        assert s3_client.mock_calls == [
            mock.call.get_paginator("list_object_versions"),
            mock.call.get_paginator().paginate(Bucket="spade", Prefix=""),
            mock.call.get_paginator("list_object_versions"),
            mock.call.get_paginator().paginate(Bucket="martello", Prefix=""),
        ]

        if dry_run:
            assert av_api_client.mock_calls == []
            assert retval == Counter({"candidate": 6})
        else:
            # taking string representations because call()s are not sortable and we want to disregard order
            assert sorted(str(c) for c in av_api_client.mock_calls) == sorted(str(c) for c in (
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "oo_.BepoodlLml"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "ooBmo_pe.ldoLl"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "molo.oB_oLdelp"),
                mock.call.scan_and_tag_s3_object("martello", "unmentionables.PNG", "lFHrwenroye_"),
                mock.call.scan_and_tag_s3_object("martello", "sandy/mount.pdf", "nHwr_elFoyre"),
                mock.call.scan_and_tag_s3_object("martello", "handy/mount.pdf", "Hn_olFerweyr"),
            ))
            assert retval == Counter({
                "candidate": 6,
                "pass": 1,
                "fail": 2,
                "already_tagged": 2,
                "error": 1,
            })

    def test_prefix_filtered_single_bucket(self, versions_page_size, dry_run, concurrency):
        av_api_client, s3_client = self._get_mock_clients(
            {
                bucket_name: tuple(v_r for v_r in versions_responses if v_r[0]["Key"].startswith("sand"))
                for bucket_name, versions_responses in self.buckets_versions_responses.items()
            },
            versions_page_size,
        )

        with ThreadPoolExecutor(max_workers=concurrency) if concurrency else nullcontext() as executor:
            map_callable = map if executor is None else executor.map
            retval = virus_scan_bucket(
                s3_client,
                av_api_client,
                ("spade",),
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
            assert retval == Counter({"candidate": 6})
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
            assert retval == Counter({
                "candidate": 6,
                "pass": 3,
                "fail": 1,
                "already_tagged": 2,
            })

    def test_prefix_filtered_multi_bucket(self, versions_page_size, dry_run, concurrency):
        av_api_client, s3_client = self._get_mock_clients(
            {
                bucket_name: tuple(v_r for v_r in versions_responses if v_r[0]["Key"].startswith("sand"))
                for bucket_name, versions_responses in self.buckets_versions_responses.items()
            },
            versions_page_size,
        )

        with ThreadPoolExecutor(max_workers=concurrency) if concurrency else nullcontext() as executor:
            map_callable = map if executor is None else executor.map
            retval = virus_scan_bucket(
                s3_client,
                av_api_client,
                ("spade", "martello",),
                prefix="sand",
                since=None,
                dry_run=dry_run,
                map_callable=map_callable,
            )

        assert s3_client.mock_calls == [
            mock.call.get_paginator("list_object_versions"),
            mock.call.get_paginator().paginate(Bucket="spade", Prefix="sand"),
            mock.call.get_paginator("list_object_versions"),
            mock.call.get_paginator().paginate(Bucket="martello", Prefix="sand"),
        ]

        if dry_run:
            assert av_api_client.mock_calls == []
            assert retval == Counter({"candidate": 7})
        else:
            # taking string representations because call()s are not sortable and we want to disregard order
            assert sorted(str(c) for c in av_api_client.mock_calls) == sorted(str(c) for c in (
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "oo_.BepoodlLml"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "moB_eLplool.do"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "ooBmo_pe.ldoLl"),
                mock.call.scan_and_tag_s3_object("spade", "sandman/1234-deedaw.pdf", "epmlLoBodo_ol."),
                mock.call.scan_and_tag_s3_object("spade", "sandman/1234-deedaw.pdf", "loleLoooBp_md."),
                mock.call.scan_and_tag_s3_object("spade", "sandman/4321-billy-winks.pdf", "molo.oB_oLdelp"),
                mock.call.scan_and_tag_s3_object("martello", "sandy/mount.pdf", "nHwr_elFoyre"),
            ))
            assert retval == Counter({
                "candidate": 7,
                "pass": 3,
                "fail": 1,
                "already_tagged": 3,
            })
