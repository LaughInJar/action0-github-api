"""The repository model (:py:class:`Repo`)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .user import SimpleUser


def _timestamp(value: str | None) -> datetime | None:
    """
    Parse one of GitHub's ISO 8601 timestamps (``2008-06-11T21:19:53Z``).

    :param value: the timestamp string, or ``None`` where GitHub sends null
    :return: the parsed datetime (timezone-aware), or ``None``
    """
    if value is None:
        return None
    return datetime.fromisoformat(value)


@dataclass
class Repo:
    """
    A GitHub repository.

    This is GitHub's ``full-repository`` schema, reduced to the commonly
    used fields (the raw payload has ~100 more).
    """

    id: int
    """The numeric repository id."""

    name: str
    """The repository name, e.g. ``"cpython"``."""

    full_name: str
    """Owner and name, e.g. ``"python/cpython"``."""

    owner: SimpleUser
    """The owning user or organization."""

    private: bool
    """Whether the repository is private."""

    html_url: str
    """The web URL, e.g. ``"https://github.com/python/cpython"``."""

    default_branch: str
    """The default branch, e.g. ``"main"``."""

    description: str | None = None
    """The description, if set."""

    language: str | None = None
    """The dominant programming language, if detected."""

    stargazers_count: int = 0
    """The number of stars."""

    forks_count: int = 0
    """The number of forks."""

    open_issues_count: int = 0
    """The number of open issues (including open pull requests)."""

    topics: list[str] | None = None
    """The repository topics, if any were requested/set."""

    archived: bool = False
    """Whether the repository is archived (read-only)."""

    created_at: datetime | None = None
    """When the repository was created."""

    updated_at: datetime | None = None
    """When the repository was last updated."""

    pushed_at: datetime | None = None
    """When the repository was last pushed to (``None`` on empty repos)."""

    @classmethod
    def from_json(cls, data: Any) -> Repo:
        """
        Build a repository from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the repository
        """
        topics = data.get("topics")
        return cls(
            id=data["id"],
            name=data["name"],
            full_name=data["full_name"],
            owner=SimpleUser.from_json(data["owner"]),
            private=data["private"],
            html_url=data["html_url"],
            default_branch=data["default_branch"],
            description=data.get("description"),
            language=data.get("language"),
            stargazers_count=data.get("stargazers_count", 0),
            forks_count=data.get("forks_count", 0),
            open_issues_count=data.get("open_issues_count", 0),
            topics=list(topics) if topics is not None else None,
            archived=data.get("archived", False),
            created_at=_timestamp(data.get("created_at")),
            updated_at=_timestamp(data.get("updated_at")),
            pushed_at=_timestamp(data.get("pushed_at")),
        )
