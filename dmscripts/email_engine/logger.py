"""Shared loggers for email_engine package

We want to ensure that certain log messages (state updates for a
email_engine.LoggingQueue) always reach the root logger.

This module creates a new log level STATE and a `state_logger` with a method
`state()` to log messages at that level. That logger is attached directly to
the root logger, so if the root logger level is STATE or higher and has a
handler attached then state updates will be logged (currently this is the
responsibility of email_engine.email_engine). We do this because we also want
to have ancillary information about the script execution in the log file
alongside the state updates; this will aid debugging issues in future.

We also create `logger` attached to the usual dmscripts logger for logging to
stderr for messages that are not state updates.
"""

import logging


# define a new log level for logging queue log levels
# not as high as INFO, but not as low as DEBUG
STATE = 15


logging.addLevelName(STATE, "STATE")


class StateLogger(logging.LoggerAdapter):
    def __init__(self, logger: logging.Logger):
        super().__init__(logger, {})

    def state(self, msg, *args, **kwargs) -> None:
        self.log(STATE, msg, *args, **kwargs)


logger = logging.getLogger("script.email_engine")
state_logger = StateLogger(logging.getLogger("email_engine_audit_logger"))

state_logger.setLevel(STATE)
