"""The label model (:py:class:`Label`)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Label:
    """
    An issue label.

    Everything but the name is optional: in some payloads (and in older
    parts of the API) GitHub sends labels as bare name strings instead of
    objects.
    """

    name: str
    """The label name, e.g. ``"bug"``."""

    id: int | None = None
    """The numeric label id."""

    color: str | None = None
    """The 6-character hex color code, without the leading ``#``."""

    description: str | None = None
    """The description, if set."""

    default: bool = False
    """Whether this is one of GitHub's default labels."""

    @classmethod
    def from_json(cls, data: Any) -> Label:
        """
        Build a label from one decoded JSON item — a full label object or
        a bare name string.

        >>> Label.from_json("bug")
        Label(name='bug', id=None, color=None, description=None, default=False)

        :param data: the decoded JSON item
        :return: the label
        """
        if isinstance(data, str):
            return cls(name=data)
        return cls(
            name=data["name"],
            id=data.get("id"),
            color=data.get("color"),
            description=data.get("description"),
            default=data.get("default", False),
        )
