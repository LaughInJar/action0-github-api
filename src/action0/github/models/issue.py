"""The issue model (:py:class:`Issue`) and its state vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from typing import Any

from .label import Label
from .timestamps import timestamp
from .user import SimpleUser

if TYPE_CHECKING:
    # imported lazily at runtime: milestone.py imports IssueState from
    # this module, so a module-level import would be circular
    from .milestone import Milestone


class IssueState(StrEnum):
    """The state of an issue."""

    OPEN = "open"
    CLOSED = "closed"


@dataclass
class Issue:
    """
    A GitHub issue.

    This is GitHub's ``issue`` schema, reduced to the commonly used
    fields. Note that GitHub's issue endpoints return pull requests too
    (every pull request is an issue) — :py:attr:`is_pull_request` tells
    them apart.
    """

    id: int
    """The numeric issue id (globally unique)."""

    number: int
    """The issue number (unique per repository), e.g. ``1347``."""

    title: str
    """The title."""

    state: IssueState
    """Whether the issue is open or closed."""

    html_url: str
    """The web URL, e.g. ``"https://github.com/python/cpython/issues/1"``."""

    user: SimpleUser | None = None
    """The author (``None`` e.g. for deleted accounts)."""

    body: str | None = None
    """The description text, if any."""

    labels: list[Label] = field(default_factory=list)
    """The labels."""

    assignees: list[SimpleUser] = field(default_factory=list)
    """The assigned users."""

    milestone: Milestone | None = None
    """The milestone the issue is assigned to, if any."""

    comments: int = 0
    """The number of comments."""

    locked: bool = False
    """Whether the conversation is locked."""

    is_pull_request: bool = False
    """Whether this "issue" actually is a pull request (GitHub's issue
    endpoints return both)."""

    created_at: datetime | None = None
    """When the issue was created."""

    updated_at: datetime | None = None
    """When the issue was last updated."""

    closed_at: datetime | None = None
    """When the issue was closed (``None`` while it is open)."""

    @classmethod
    def from_json(cls, data: Any) -> Issue:
        """
        Build an issue from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the issue
        """
        from .milestone import Milestone

        user = data.get("user")
        milestone = data.get("milestone")
        return cls(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            state=IssueState(data["state"]),
            html_url=data["html_url"],
            user=SimpleUser.from_json(user) if user is not None else None,
            body=data.get("body"),
            labels=[Label.from_json(item) for item in data.get("labels", [])],
            assignees=[SimpleUser.from_json(item) for item in data.get("assignees", [])],
            milestone=Milestone.from_json(milestone) if milestone is not None else None,
            comments=data.get("comments", 0),
            locked=data.get("locked", False),
            # pull requests carry a "pull_request" key with their PR URLs
            is_pull_request="pull_request" in data,
            created_at=timestamp(data.get("created_at")),
            updated_at=timestamp(data.get("updated_at")),
            closed_at=timestamp(data.get("closed_at")),
        )
