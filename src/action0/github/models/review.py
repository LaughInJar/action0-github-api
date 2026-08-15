"""The pull request review models (:py:class:`Review`, :py:class:`ReviewComment`)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from .timestamps import timestamp
from .user import SimpleUser


class ReviewState(StrEnum):
    """The state of a pull request review — uppercase on the wire,
    unlike every other GitHub state vocabulary."""

    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    COMMENTED = "COMMENTED"
    DISMISSED = "DISMISSED"
    PENDING = "PENDING"


@dataclass
class Review:
    """
    A pull request review — an approval, change request or review
    comment thread anchor.
    """

    id: int
    """The numeric review id (globally unique)."""

    state: ReviewState
    """The review verdict."""

    html_url: str
    """The web URL of the review."""

    user: SimpleUser | None = None
    """The reviewer (``None`` e.g. for deleted accounts)."""

    body: str = ""
    """The summary text (may be empty, e.g. on a plain approval)."""

    commit_id: str | None = None
    """The commit the review refers to."""

    submitted_at: datetime | None = None
    """When the review was submitted (``None`` while it is
    :py:attr:`~ReviewState.PENDING`)."""

    @classmethod
    def from_json(cls, data: Any) -> Review:
        """
        Build a review from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the review
        """
        user = data.get("user")
        return cls(
            id=data["id"],
            state=ReviewState(data["state"]),
            html_url=data["html_url"],
            user=SimpleUser.from_json(user) if user is not None else None,
            body=data.get("body") or "",
            commit_id=data.get("commit_id"),
            submitted_at=timestamp(data.get("submitted_at")),
        )


@dataclass
class ReviewComment:
    """
    A pull request *review* comment — a comment anchored to a line of
    the diff. Not to be confused with the conversation comments
    (:py:class:`~action0.github.models.comment.IssueComment` — a pull
    request's conversation is its issue's comment thread).
    """

    id: int
    """The numeric comment id (globally unique)."""

    path: str
    """The file the comment is anchored to."""

    body: str
    """The comment text (GitHub-flavored Markdown)."""

    html_url: str
    """The web URL of the comment."""

    user: SimpleUser | None = None
    """The author (``None`` e.g. for deleted accounts)."""

    line: int | None = None
    """The line in the diff the comment is anchored to (``None`` when
    the comment is outdated — the code has changed since)."""

    diff_hunk: str | None = None
    """The diff excerpt the comment was made on."""

    commit_id: str | None = None
    """The commit the comment refers to."""

    created_at: datetime | None = None
    """When the comment was created."""

    updated_at: datetime | None = None
    """When the comment was last edited."""

    @classmethod
    def from_json(cls, data: Any) -> ReviewComment:
        """
        Build a review comment from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the review comment
        """
        user = data.get("user")
        return cls(
            id=data["id"],
            path=data["path"],
            body=data["body"],
            html_url=data["html_url"],
            user=SimpleUser.from_json(user) if user is not None else None,
            line=data.get("line"),
            diff_hunk=data.get("diff_hunk"),
            commit_id=data.get("commit_id"),
            created_at=timestamp(data.get("created_at")),
            updated_at=timestamp(data.get("updated_at")),
        )
