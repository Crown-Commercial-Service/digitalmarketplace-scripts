from pathlib import Path
from unittest import mock

import pytest


class TestArgumentParser:

    @pytest.fixture
    def argument_parser_factory(self, default_argument_parser_factory):
        return default_argument_parser_factory

    def test_dry_run(self, argument_parser_factory):
        argument_parser = argument_parser_factory()
        assert argument_parser.parse_args([]).dry_run is False
        assert argument_parser.parse_args(["--dry-run"]).dry_run is True
        assert argument_parser.parse_args(["-n"]).dry_run is True

    def test_notify_api_key_from_envvar(self, argument_parser_factory):
        with mock.patch.dict("os.environ", {"DM_NOTIFY_API_KEY": "test-api-key"}):
            args = argument_parser_factory().parse_args([])

        assert args.notify_api_key == "test-api-key"

    def test_notify_api_key_from_envvar_and_argv(self, argument_parser_factory):
        with mock.patch.dict("os.environ", {"DM_NOTIFY_API_KEY": "old-api-key"}):
            args = argument_parser_factory().parse_args(
                ["--notify-api-key=new-api-key"]
            )

        assert args.notify_api_key == "new-api-key"

    def test_notify_api_key_is_none_if_not_set_by_environment_or_cli(self, argument_parser_factory):
        with mock.patch.dict("os.environ", clear=True):
            args = argument_parser_factory().parse_args([])

        assert args.notify_api_key is None

    def test_reference_default_startswith_sys_argv_0(self, argument_parser_factory):
        with mock.patch("sys.argv", ["foobar"]):
            args = argument_parser_factory().parse_args()

        assert args.reference.startswith("foobar")

    def test_reference_default_suffix_changes_if_argv_changes(self, argument_parser_factory):
        with mock.patch("sys.argv", ["foobar"]):
            args = argument_parser_factory().parse_args()
            assert args.reference == "foobar-6a2639d8"

        with mock.patch("sys.argv", ["foobar", "-n", "--notify-api-key=0000"]):
            args = argument_parser_factory().parse_args()
            assert args.reference == "foobar-3c3adfeb"

    def test_reference_default_suffix_does_not_depend_on_order_of_args(self, argument_parser_factory):
        with mock.patch("sys.argv", ["foobar", "-n", "--notify-api-key=0000"]):
            args1 = argument_parser_factory().parse_args()

        with mock.patch("sys.argv", ["foobar", "--notify-api-key=0000", "-n"]):
            args2 = argument_parser_factory().parse_args()

        assert args1.reference == args2.reference

    def test_reference_default_removes_suffix_dot_py(self, argument_parser_factory):
        with mock.patch("sys.argv", ["foobar.py"]):
            args = argument_parser_factory().parse_args([])

        assert args.reference == "foobar-6a2639d8"

    def test_reference_default_removes_path_components(self, argument_parser_factory):
        with mock.patch("sys.argv", ["./scripts/foobar"]):
            args = argument_parser_factory().parse_args([])

        assert args.reference == "foobar-6a2639d8"

    def test_reference_default_prefix_overridable_by_factory_arg(self, argument_parser_factory):
        with mock.patch("sys.argv", ["foo"]):
            args = argument_parser_factory(reference="bar").parse_args([])

        assert args.reference == "bar"

    def test_reference_cli_argument_overrides_factory_arg(self, argument_parser_factory):
        with mock.patch("sys.argv", ["foo"]):
            args = argument_parser_factory(reference="bar").parse_args(
                ["--reference=baz"]
            )

        assert args.reference == "baz"

    def test_default_logfile_path_is_derived_from_reference(self, argument_parser_factory):
        with mock.patch("sys.argv", ["foo"]):
            args = argument_parser_factory().parse_args([])

        assert args.logfile == Path("/tmp/foo-f55be76c.log")

        with mock.patch("sys.argv", ["foo"]):
            args = argument_parser_factory(reference="bar").parse_args([])

        assert args.logfile == Path("/tmp/bar.log")
