"""Types and classes for typing Notify calls

We want to be able to use static typing on email_engine so that coding mistakes
can be caught before run time.

Also, we create some classes to help with saving a notification to a file and
reading it back into memory in a human readable fashion.
"""

from ast import literal_eval
from typing import Callable, Dict, Generator, Union


class EmailNotification(dict):
    """A typed, hashable, serder-able, frozen dict subclass

    This class packages the arguments to to
    NotificationsAPIClient.send_email_notification()

    It supports the following behaviours we need to support email_engine
    functionality:

        - compare two notifications to remove duplicates
        - allow using notifications as keys to a dictionary
        - write and read a human-readable string representation
    """

    def __init__(
        self,
        *,
        email_address: str,
        template_id: str,
        personalisation: Dict[str, str] = None
    ):
        super().__init__(
            email_address=email_address,
            template_id=template_id,
            personalisation=personalisation,
        )

    def __setitem__(self, key: str, value: str) -> None:
        raise RuntimeError("EmailNotification instances are frozen")

    def __hash__(self) -> int:  # type: ignore[override]  # noqa: F821
        # dicts are usually unhashable, but we want to use EmailNotifications
        # as the key to another dict, so we cheat and find the hash of the
        # string representation. The order of keys is going to be important for
        # this, so we make it explicit
        return (
            dict(
                email_address=self["email_address"],
                template_id=self["template_id"],
                personalisation=self["personalisation"],
            )
            .__repr__()
            .__hash__()
        )

    @classmethod
    def from_str(cls, s: str) -> "EmailNotification":
        """Parse a dict literal representation of a notification"""
        return cls(**literal_eval(s))


class NotificationResponse(dict):
    @classmethod
    def from_str(cls, s: str) -> "NotificationResponse":
        """parse a dict literal representation of a NotificationResponse"""
        return cls(**literal_eval(s))


NotificationsGenerator = Generator[EmailNotification, None, None]
NotificationsGeneratorFunction = Callable[..., NotificationsGenerator]
Notifications = Union[NotificationsGenerator, NotificationsGeneratorFunction]
