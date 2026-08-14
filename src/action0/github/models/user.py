"""The user model (:py:class:`SimpleUser`), as GitHub embeds it in other resources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SimpleUser:
    """
    A user (or organization) as embedded in other GitHub resources, e.g.
    as the ``owner`` of a repository.

    This is GitHub's ``simple-user`` schema, reduced to the fields the
    shipped operations use.
    """

    login: str
    """The login name, e.g. ``"python"``."""

    id: int
    """The numeric user id."""

    html_url: str
    """The profile URL, e.g. ``"https://github.com/python"``."""

    type: str
    """``"User"`` or ``"Organization"``."""

    @classmethod
    def from_json(cls, data: Any) -> SimpleUser:
        """
        Build a user from one decoded JSON object.

        >>> SimpleUser.from_json(
        ...     {
        ...         "login": "python",
        ...         "id": 1525981,
        ...         "html_url": "https://github.com/python",
        ...         "type": "Organization",
        ...     }
        ... )
        SimpleUser(login='python', id=1525981, html_url='https://github.com/python', type='Organization')

        :param data: the decoded JSON object
        :return: the user
        """
        return cls(
            login=data["login"],
            id=data["id"],
            html_url=data["html_url"],
            type=data["type"],
        )
