"""Takes a source of notifications to be sent and logs sending them so we can
easily re-run if something breaks

This module mainly exists to seperate the process logic from outputs and
inputs, so we can unit test the logic. It shouldn't be used outside of
EmailEngine or tests. It doesn't handle anything that interacts with the
outside world (except logging), and takes more generic types.

Most of the work happens in this module happens in the `run()` function. You
really shouldn't use the LoggingQueue class outside of run() and tests.
Creating a LoggingQueue doesn't do much.

Design notes
------------

This code is designed specifically for the email_engine use case, so it is less
generic than it perhaps could be.

Currently this module doesn't do error handling or recovery, or allow for any
concurrency. Whether or not this module should handle those things is an open
question.

At the moment there is also an implicit state machine whose logic is shared
between LoggingQueue and run(). LoggingQueue could probably be tweaked to make
it clearer that, for instance, you shouldn't put notifications in the queue
after resuming from a logfile, but rather than spending a lot of time thinking
about the best API design I just decided to encapsulate it in the run()
function.  With some more thought perhaps the LoggingQueue could be made to
enforce the state logic itself.
"""

from collections import deque
from pathlib import Path
from typing import (
    Callable,
    Dict,
    Deque,
    Iterable,
    Tuple,
)
import sys

from .typing import EmailNotification, NotificationResponse
from .logger import logger, state_logger


def run(
    send_email_notification: Callable[[EmailNotification], NotificationResponse],
    *,
    notifications: Iterable[EmailNotification],
    logfile: Path,
) -> Dict[EmailNotification, NotificationResponse]:
    """Send notifications using `send_email_notification`

    Reads email notifications from `notifications`, then sends them using
    `send_email_notification`. When a notification is read from the iterable it
    is logged, and when a notification is sent it is again logged.

    Progress is logged using the built-in logging module; `logfile` should be
    attached to a file handler so that the state is saved to disk.

    If `logfile` contains logging messages from a previous call, then
    `notifications` will be discarded without being iterated. This should mean
    that this function is idempotent.
    """
    queue = LoggingQueue()

    resuming, exhausted = queue.put_from_logfile(logfile)

    # If you are doing a a re-run and the iterator of notifications in the
    # original run was exhausted, then we don't iterate again.
    #
    # If the notifications are being output by a generator (and they should
    # be) then this has some nice side-effects:
    #
    # 1. runs are deterministic, you always know the same people will be emailed
    # 2. re-runs don't need to make API calls to DMp and so are faster
    # 3. you can make the generator non-idempotent if you really want to
    #
    # The downside is how do you handle the scenario where the original
    # generator wasn't exhausted... for now we just crash.
    if resuming and not queue.todo:
        logger.info("nothing left to do! exiting")
        sys.exit(0)

    elif queue.todo and exhausted:
        # throw the generator away
        logger.info("resuming from log file")
        del notifications

    elif queue.todo and not exhausted:
        # not sure what to do in this situation, maybe in future we can add a flag to proceed anyway
        raise RuntimeError(
            "in the logs for the original run the notifications generator was not exhausted, refusing to proceed"
        )

    elif not resuming:
        state_logger.info("OFFICIAL SENSITIVE - do not distribute - this file contains email addresses and other PII")
        logger.info("getting notifications to send from API")
        queue.put_from(notifications)

    else:
        # this should never be reached
        assert True, "non-exhaustive if-else statement"

    # main loop
    # this could probably be asynchronous
    try:
        while queue.todo:
            queue.send_next(send_email_notification)
    except Exception as e:
        # we want to log how many are left to send
        logger.warning(
            f"sending emails was stopped by {e.__class__.__name__} with {len(queue.todo)} notifications left to send"
        )
        raise

    return queue.done


class LoggingQueue:
    """Queue that streams state to logs and can be recreated from logs

    Thread-safety
    -------------

    Sending is (probably) currently thread-safe because of the design of
    `send_next()` (but it has not been proven to be so). Because we need to log
    when the notification has been sent (and we want to log the API response),
    rather than letting users get a notification from the queue and then
    requiring them to give us the response, we just ask them to give us the
    callable they would use anyway. This does means that the interface for
    LoggingQueue is a bit more `concurrent.futures.Executor` than
    `queue.Queue`, but it makes things simpler in the end.

    Putting is currently not thread-safe, because the de-duplication can cause
    a race condition. This could be fixed with a lock, or (better) by
    using different primitives, or (best) maybe by not allowing putting at all.
    """

    send_msg = "queue update: send notification {notification} response {response}"
    put_msg = "queue update: queued notification {notification}"
    put_from_msg = (
        "queue update: generator is exhausted, read {count} notifications into queue"
    )

    def __init__(self) -> None:
        self.todo: Deque[EmailNotification] = deque()
        self.done: Dict[EmailNotification, NotificationResponse] = {}

    def __contains__(self, notification: EmailNotification) -> bool:
        """Return true if `notification` has been queued or sent"""
        return notification in self.todo or notification in self.done

    def put(self, notification: EmailNotification, *, log=True) -> None:
        """Put `notification` into the queue

        Logs `repr(notification)` when it is added to the queue if `log` is
        true. If `notification` has already been queued or sent, does nothing.
        """

        # TODO: make this thread-safe
        if notification in self:
            logger.warning(f"ignoring duplicate notification {notification}")
            return

        self.todo.append(notification)

        if log:
            state_logger.state(self.put_msg.format(notification=notification))

    def send_next(
        self,
        send_email_notification: Callable[[EmailNotification], NotificationResponse],
    ) -> None:
        """Send the next notification in the queue

        Calls `send_email_notification()` with the next notification in the
        queue and logs the result of the call.
        """

        # TODO: this should be thread-safe, test that it is
        notification = self.todo.popleft()
        logger.debug(f"popping notification {notification} to send it")
        assert notification not in self, "duplicate notification in queue"

        response = send_email_notification(notification)

        state_logger.state(self.send_msg.format(notification=notification, response=response))

        self.done[notification] = response

    def put_from(self, notifications: Iterable[EmailNotification]) -> int:
        """Put notifications from the iterable into the queue

        :returns: the number of notifications added to the queue
        """
        count = 0
        for notification in notifications:
            # TODO: this is a hack to allow a plain dict
            # it can be removed with a postional only arg
            # in EmailNotification.__init__
            # when on Python 3.8
            self.put(EmailNotification(**notification))
            count += 1
        state_logger.state(self.put_from_msg.format(generator=notifications, count=count))
        return count

    def put_from_logfile(self, f: Path) -> Tuple[int, bool]:
        """Reload queue from log file `f`

        If the log file contains log messages from a `LoggingQueue` then try
        and recreate the state based on the log messages.

        This function returns two values. The first is the number of
        notifications added to the queue (but not the number of notifications
        outstanding!). It is mainly useful to be able to tell whether there was
        a previous run in the log file or not. The second is a bool that
        indicates whether the previous queue had been interrupted while adding
        notifications from an iterable with `put_from()`; if the second return
        value is false then that means that whatever was adding notifications
        to the queue wasn't finished doing so.

        :returns: the number of notifications added to the queue and whether
                  the previous had completed all `put_from()` calls successfully
        """
        # we read the whole file into memory at once to avoid reading our own tail
        loglines = f.read_text().splitlines()
        if not loglines:
            return 0, False
        logger.info(f"logging queue reading from logfile {f}")
        return self._read_log(loglines)

    def _read_log(self, logstream: Iterable[str]) -> Tuple[int, bool]:
        count = 0
        line_count = 0
        exhausted = False

        # this is a hand-crafted parser for log lines
        # maybe it could be generated from the format spec?
        for logline in logstream:
            # ignore lines that don't begin with the magic words
            # (modulo any prefixes from logging)
            magic_words = "queue update: "
            if magic_words not in logline:
                continue

            update = logline[logline.find(magic_words) + len(magic_words):]

            if update.startswith("queued"):
                notification = EmailNotification.from_str(
                    update[len("queued notification "):]
                )
                self.put(notification, log=False)
                count += 1
            elif update.startswith("send"):
                # this will probably break if notification personalisation
                # contains the word "response"
                notification = EmailNotification.from_str(
                    update[len("send notification "):update.find(" response ")]
                )
                response = NotificationResponse.from_str(
                    update[update.find(" response ") + len(" response "):]
                )

                if notification not in self.todo:
                    raise RuntimeError(
                        f"log is invalid, notification {notification} was sent before it was queued"
                    )

                self.todo.remove(notification)
                self.done[notification] = response
            elif update.startswith("generator is exhausted"):
                exhausted = True
                original_count = int(
                    update[
                        len("generator is exhausted, read "):
                        update.find("notifications")
                    ]
                )
                assert original_count == len(self.todo) + 2 * len(
                    self.done
                ), "number of log lines parsed does not match number of notifications originally queued"
            else:
                raise RuntimeError(f"unable to parse log line {logline}")

            line_count += 1

        assert (
            line_count == len(self.todo) + 2 * len(self.done) + exhausted
        ), "number of log lines parsed does not match number of notifications queued"

        if line_count:
            logger.debug(
                f"logging queue read {line_count} log lines"
            )
            logger.info(
                f"queue has {len(self.todo)} notifications outstanding and {len(self.done)} already sent"
            )

        return count, exhausted
