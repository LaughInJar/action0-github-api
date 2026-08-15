"""The issue comment model (:py:class:`IssueComment`)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .timestamps import timestamp
from .user import SimpleUser


@dataclass
class IssueComment:
    """
    A comment on an issue.

    This is GitHub's ``issue-comment`` schema, reduced to the commonly
    used fields. Pull request conversation comments are issue comments
    too (every pull request is an issue) — only review comments, the
    ones anchored to a diff line, live in a separate API.
    """

    id: int
    """The numeric comment id (globally unique)."""

    html_url: str
    """The web URL, e.g.
    ``"https://github.com/octo/demo/issues/1#issuecomment-1"``."""

    body: str
    """The comment text (GitHub-flavored Markdown)."""

    user: SimpleUser | None = None
    """The author (``None`` e.g. for deleted accounts)."""

    created_at: datetime | None = None
    """When the comment was written."""

    updated_at: datetime | None = None
    """When the comment was last edited."""

    @classmethod
    def from_json(cls, data: Any) -> IssueComment:
        """
        Build a comment from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the comment
        """
        user = data.get("user")
        return cls(
            id=data["id"],
            html_url=data["html_url"],
            body=data.get("body", ""),
            user=SimpleUser.from_json(user) if user is not None else None,
            created_at=timestamp(data.get("created_at")),
            updated_at=timestamp(data.get("updated_at")),
        )
