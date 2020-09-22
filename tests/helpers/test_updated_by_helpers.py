from unittest import mock

import pytest

from dmscripts.helpers.updated_by_helpers import get_user


@pytest.fixture(autouse=True)
def environ():
    with mock.patch.dict("os.environ", {}, clear=True):
        import os
        yield os.environ


@pytest.fixture
def subprocess_run():
    with mock.patch("dmscripts.helpers.updated_by_helpers.subprocess.run") as run:
        yield run


def test_get_user_can_use_jenkins_envvars(environ):
    environ["JENKINS_HOME"] = "/var/lib/jenkins"
    environ["BUILD_TAG"] = "jenkins-Do a thing-100"
    environ["BUILD_USER"] = "Reginald Jeeves"

    assert get_user() == "jenkins-Do a thing-100 started by Reginald Jeeves"

    # BUILD_USER relies on a plugin that needs to be enabled for each job, so
    # we should check get_user() works even if BUILD_USER isn't present for
    # some reason
    del environ["BUILD_USER"]

    assert get_user() == "jenkins-Do a thing-100"


def test_get_user_can_use_git_user_email(subprocess_run):
    proc = mock.Mock()
    proc.return_code = 0
    proc.stdout = "user.name@example.com"
    subprocess_run.return_value = proc

    assert get_user() == "user.name@example.com"


def test_get_user_fallsback_to_username_if_git_not_installed(environ, subprocess_run):
    environ["USERNAME"] = "cheeseshop"
    subprocess_run.side_effect = FileNotFoundError

    assert get_user() == "cheeseshop"
