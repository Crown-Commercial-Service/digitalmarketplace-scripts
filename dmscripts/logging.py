from __future__ import absolute_import

import sys
import logging
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL  # noqa

from dmutils.logging import CustomLogFormatter

LOG_FORMAT = '%(asctime)s %(name)s %(levelname)s %(message)s'


def configure_logger(log_levels=None):
    """Configure logging handlers and return a configured 'script' logger

    :param log_levels: a dictionary of logger name and corresponding log
                       levels. Can be used to silence or add additional log
                       output from other packages. By default configures
                       'script' and 'dmutils' loggers with INFO level.

    :return: 'script' logger object

    """
    log_levels = merge_log_levels(log_levels or {})

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(CustomLogFormatter(LOG_FORMAT))

    for logger_name, level in log_levels.items():
        logging.getLogger(logger_name).addHandler(handler)
        logging.getLogger(logger_name).setLevel(level)

    return logging.getLogger('script')


def merge_log_levels(added_log_levels):
    log_levels = {
        'dmutils': INFO,
        'dmapiclient': INFO,
        'script': INFO,
    }

    log_levels.update(added_log_levels)

    return log_levels
