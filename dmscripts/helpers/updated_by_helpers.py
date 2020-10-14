import getpass
import os
import subprocess


def get_user() -> str:
    """Find the name of the user running the script for audit purposes

    Digital Marketplace API methods typically take a `user` or `updated_by`
    parameter that is used to record who or what made a particular change. This
    function uses a number of heuristics to generate this automatically, to
    save the script caller having to do it themselves.
    """

    # if the script is running on Jenkins use the build vars
    if os.getenv("JENKINS_HOME") and os.getenv("BUILD_TAG"):
        updated_by = os.environ["BUILD_TAG"]
        if os.getenv("BUILD_USER"):
            updated_by += f' started by {os.environ["BUILD_USER"]}'
        return updated_by

    # if possible get the email address from git config
    try:
        proc = subprocess.run(
            ["git", "config", "--get", "user.email"],
            stdout=subprocess.PIPE, universal_newlines=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    else:
        git_user_email = proc.stdout.strip()
        return git_user_email

    # fallback to username, in general this is less preferred
    return getpass.getuser()
