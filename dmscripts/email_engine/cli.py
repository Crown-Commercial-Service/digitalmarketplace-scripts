"""Standard command line arguments for an email script

For notes on how this module works for a user running a script, have a look at
the docstring for the email_engine module.

Scripts that send emails tend to have a lot of options in common; this module
gathers them together to reduce repetition and increase consistency.

The main function is `argument_parser_factory()`: it takes a bunch of keyword
arguments that configure how the command line will appear. It returns a
subclass of `argparse.ArgumentParser`, so you can configure the command line
more if necessary before parsing args.

For some command line options, we want to allow values to be supplied by
environment variable as well as a flag; the `EnvDefaultAction` class supports
this.

Running this module will show the default command line arguments::
    python dmscripts/email_engine/cli.py
"""
from pathlib import Path
import argparse
import hashlib
import os
import sys


__all__ = ["argument_parser_factory"]


def argument_parser_factory(
    *, reference: str = None, logfile: Path = None, **kwargs
) -> argparse.ArgumentParser:
    """Create an ArgumentParser to read options for an email script

    Feel free to add command line arguments to this function, you may want to
    put them behind a kwarg flag if they are not needed for all scripts.
    Remember to document them here so that script writers know about them, you
    can avoid duplication by not adding them to the function signature though.

    :param reference: default reference if none is supplied at command line,
        if None the script name will be used, plus a hash of the arguments
    :param logfile: default path to the logfile if none is supplied at command line,
        if None /tmp/<reference>.log will be used

    :param description: Text to display before the argument help
    :param epilog: Text to display after the argument help

    :param stage_required: If true then parser will raise an exception if stage
        cannot be found from the environment or command line (default: true).
    :param notify_api_key_required: If true then parser will raise an exception
        if a Notify API key cannot be found from the environment or command line
        (default: true).
    :param notify_template_id_required: Some scripts may expect to a template
        ID be supplied on the command line, rather than have it hardcoded. If
        notify_template_id_required is true then the command line arguments will
        include a required flag to specify the template ID (default: false).
    """

    # Generate the default reference from sys.argv. This does mean you will
    # need to mock sys.argv when calling argument_parser_factory in tests.
    if reference is None:
        reference = Path(sys.argv[0]).stem
        reference_is_default = True
    else:
        reference_is_default = False

    p = _ArgumentParser(
        description=kwargs.get("description"),
        epilog=kwargs.get("epilog"),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    p.add_argument(
        "-n", "--dry-run", action="store_true", help="Do not send notifications."
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print more detail about what the script is doing.",
    )

    p.add_argument(
        "--stage",
        action=EnvDefault,
        choices=["local", "preview", "staging", "production"],
        envvar="DM_ENVIRONMENT",
        help="Stage/environment to make API calls to. Can also be set with environment variable DM_ENVIRONMENT.",
        required=kwargs.get("stage_required", True),
    )

    if kwargs.get("notify_template_id_required") is True:
        p.add_argument(
            "--notify-template-id",
            help="Notify template ID for notifications.",
            required=True,
        )

    p.add_argument(
        "--notify-api-key",
        action=EnvDefault,
        envvar="DM_NOTIFY_API_KEY",
        help="Can also be set with environment variable DM_NOTIFY_API_KEY.",
        required=kwargs.get("notify_api_key_required", True),
    )

    p.add_argument(
        "--reference",
        default=reference,
        type=append_hash_of_argv if reference_is_default else None,  # Only append hash if no reference specified
        help=(
            "Identifer to reference all the emails sent by this script (sent to Notify)."
            " Defaults to the name of the script, plus a hash of the arguments."
        ),
    )

    # As this log will contain PII, we want to make sure it doesn't sit on
    # a developers drive for too long, however, we do need to be able to
    # find the logs again for resuming a run or for audit purposes.
    #
    # So for a default we just go ahead and assume that there is a /tmp folder,
    # which is true everywhere except Windows.
    p.add_argument(
        "--logfile",
        # the handling of this argument is a little special, see _ArgumentParser
        default=logfile or "/tmp/{reference}.log",
        help=(
            "File where log messages will be saved so that the script can resume if interrupted."
            " By default logs are saved in the system tmp folder with the name of the script."
        ),
    )

    return p


def append_hash_of_argv(reference: str) -> str:
    # Add a hash of the command line arguments to the reference so running the
    # same script with different arguments results in a different reference.
    args = [reference] + sorted(sys.argv[1:])
    arghash = hashlib.blake2b(
        " ".join(args).encode(), digest_size=4
    ).hexdigest()
    return f"{reference}-{arghash}"


# copied from https://stackoverflow.com/a/10551190
class EnvDefault(argparse.Action):
    def __init__(self, envvar, required=True, default=None, **kwargs):
        if not default and envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


# We subclass `argparse.ArgumentParser` to add a small bit of specialised
# functionality; we want the logfile to default to a file with the same name as
# the reference, but we won't know the reference until all the arguments are
# parsed; the only way I could find to achieve this is to tweak `parse_args()`.
#
class _ArgumentParser(argparse.ArgumentParser):
    def parse_known_args(self, args=None, namespace=None):
        namespace, args = super().parse_known_args(args, namespace)
        if isinstance(namespace.logfile, str) and "{reference}" in namespace.logfile:
            namespace.logfile = namespace.logfile.format(reference=namespace.reference)
        namespace.logfile = Path(namespace.logfile)
        return namespace, args


if __name__ == "__main__":
    argument_parser_factory().parse_args(["--help"])
