"""Framework for sending emails from scripts via Notify

This module aims to reduce a lot of the boilerplate involved in writing a
script that sends a batch of emails using Notify.

It handles

    - most command line arguments
    - logging
    - recovery/resume after failures
    - sending requests to Notify

The theory is that the email script logs notifications to be sent to a log
file, so that if the script fails partway through it can read the logfile and
pick up where it left off.

Note that this log will contain Personally Identifiable Information, so by
default it is saved in the `tmp` folder where it shouldn't stick around for
more than a week.

All emails sent with email_engine will have the same Notify reference; by
default (see email_engine.cli) this is the name of the script (sys.argv[0]).
The reference is also used as the name of the logfile by default.

How to use as a script runner
-----------------------------

For each script the command line arguments will vary slightly, but some
arguments will be common to all and enforced by `email_engine.cli`.

Sending notifications via Notify requires a Notify API key; this can be
supplied either using the DM_NOTIFY_API_KEY environment variable, or the
--notify-api-key command line flag.

Normally a script will also need to know which environment to make API calls
to; this can be supplied using the DM_ENVIRONMENT environment variable, or the
--stage command line flag.

Both the reference and the logfile path can be overridden at the command line,
with the `--reference` and `--logfile` flags.

How to use as a script writer
-----------------------------

For the developer writing a script, the only function you *need* from this
module is `email_engine()`; given a generator that yields dictionaries with
details of notifications to send, it will take care of the rest::

    from dmapiclient import DataAPIClient
    from dmscripts.email_engine import email_engine

    def notifications(stage, **kwargs):
        # generate emails to be sent by calling the DMp API
        # and email_engine will deal with sending them for you
        data_api_client = DataAPIClient.from_stage(stage)
        for ... in data_api_client.find_some_iter(...):
            yield {
                "email_address": ...,
                "template_id": ...,
                "personalisation": ...
            }

    if __name__ == "__main__":
        email_engine(notifications)

The email_engine package knows about common options that a generator might
need, such as the DMp environment to connect the API client to, and will call
the generator with all of those options as keyword arguments. See the `cli`
module in this package for details on what options are available.

You can override some defaults by adding keyword arguments to the
`email_engine()` call; for instance, if you want to use a different string for
the default reference and require the script runner to provide a template ID on
the command line, you can call::

    email_engine(
        notifications,
        reference="my-reference",
        notify_template_id_required=True
    )

As a script writer, if you need to add command line arguments that aren't
included by default or aren't used by any other scripts, you can customise the
argument parser before `email_engine()` uses it::

    from dmapiclient import DataAPIClient
    from dmscripts.email_engine import argument_parser_factory, email_engine

    def notifications(stage, **kwargs):
        ...

    if __name__ == "__main__":
        arg_parser = argument_parser_factory()
        arg_parser.add_argument(...)
        args = arg_parser.parse_args()
        email_engine(notifications, args=args)

See scripts/notify-suppliers-of-awarded-briefs.py for a more detailed example.

For more complicated scenarios you can also start the generator yourself::

    from dmapiclient import DataAPIClient
    from dmscripts.email_engine import argument_parser_factory, email_engine

    def notifications(stage, **kwargs):
        ...

    if __name__ == "__main__":
        arg_parser = argument_parser_factory()
        arg_parser.add_argument(...)
        args = arg_parser.parse_args()
        email_engine(
            notifications(args.stage, some_other_global),
            args=args
        )
"""
from pathlib import Path
import argparse
import logging

from notifications_python_client.notifications import NotificationsAPIClient

from dmscripts.helpers.logging_helpers import configure_logger

from .cli import argument_parser_factory
from .typing import EmailNotification, NotificationResponse, Notifications
from .logger import STATE, logger
from .queue import run


def email_engine(
    notifications: Notifications,
    *,
    args: argparse.Namespace = None,
    **kwargs,
):
    """Send emails via Notify

    Send emails produced by generator function `notifications` and log progress to disk.
    If interrupted `email_engine()` has the ability to resume by reading its own log file.

    Any keyword arguments are passed to `argument_parser_factory()`, so the
    command line can be simply customised. For instance, to override the default reference,
    you can use `email_engine(notifications, reference="my-reference")`.

    :param notifications: a generator that yields `EmailNotification`s to send
    :param args: parsed command line arguments, if not provided email_engine.cli will be used to parse sys.argv
    """

    if args is None:
        # get the configuration from the command line arguments
        args = argument_parser_factory(**kwargs).parse_args()

    reference: str = args.reference
    logfile: Path = args.logfile

    # configure logging
    #
    loglevel = logging.INFO if args.verbose else logging.WARN
    configure_logger({"dmapiclient": loglevel})

    # We add the logfile handler to the root logger so all useful information
    # will be captured to the file.
    #
    root_logger = logging.getLogger()
    log_handler = logging.FileHandler(logfile)
    root_logger.addHandler(log_handler)
    root_logger.setLevel(STATE)
    #
    # Note: you might notice that in a log file there are log messages with
    # un-interpolated format strings, for example you might see:
    #
    #     {api_method} request on {api_url} finished in {api_time}
    #
    # On seeing this you might think, oh, I need to add CustomLogFormatter to
    # the log handler. Well guess what: you can't. Doing so would mean that all
    # of our state messages with dictionaries using curly braces will try and
    # be formatted as if they were referencing fields, and that will fail, and
    # then you will just get an error message saying `failed to format log
    # message`. So don't do that.

    # prepare the state, call the generator (if not already called) with the
    # command line arguments as keyword arguments
    if callable(notifications):
        notifications = notifications(**vars(args))

    notify_client = NotificationsAPIClient(args.notify_api_key)

    if args.dry_run:

        def send_email_notification(
            notification: EmailNotification,
        ) -> NotificationResponse:
            logger.info(f"[DRY-RUN] would send email notification {notification}")
            return NotificationResponse()

    else:

        def send_email_notification(
            notification: EmailNotification,
        ) -> NotificationResponse:
            # note that all notifications will have the same reference
            return notify_client.send_email_notification(
                **notification,
                reference=reference,
            )

    try:
        # do the thing
        done = run(
            send_email_notification, notifications=notifications, logfile=logfile
        )
    except KeyboardInterrupt:
        logger.critical("email engine interrupted by user")

    logger.info(f"sent {len(done)} email notifications with reference {reference}")
