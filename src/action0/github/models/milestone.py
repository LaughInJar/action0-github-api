"""The milestone model (:py:class:`Milestone`)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .issue import IssueState
from .timestamps import timestamp


@dataclass
class Milestone:
    """
    An issue milestone.

    This is GitHub's ``milestone`` schema, reduced to the commonly used
    fields. A milestone shares the issue open/closed state vocabulary
    (:py:class:`~action0.github.models.issue.IssueState`).
    """

    id: int
    """The numeric milestone id (globally unique)."""

    number: int
    """The milestone number (unique per repository) — what issue
    filters and updates refer to."""

    title: str
    """The title, e.g. ``"v1.0"``."""

    state: IssueState
    """Whether the milestone is open or closed."""

    html_url: str
    """The web URL."""

    description: str | None = None
    """The description, if set."""

    open_issues: int = 0
    """The number of open issues assigned to the milestone."""

    closed_issues: int = 0
    """The number of closed issues assigned to the milestone."""

    due_on: datetime | None = None
    """The due date, if one was set."""

    created_at: datetime | None = None
    """When the milestone was created."""

    @classmethod
    def from_json(cls, data: Any) -> Milestone:
        """
        Build a milestone from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the milestone
        """
        return cls(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            state=IssueState(data["state"]),
            html_url=data["html_url"],
            description=data.get("description"),
            open_issues=data.get("open_issues", 0),
            closed_issues=data.get("closed_issues", 0),
            due_on=timestamp(data.get("due_on")),
            created_at=timestamp(data.get("created_at")),
        )
