"""The organization models (:py:class:`Organization`,
:py:class:`SimpleOrganization`)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .timestamps import timestamp


@dataclass
class SimpleOrganization:
    """
    An organization as GitHub's membership listings send it
    (``organization-simple`` — notably *without* profile fields or even
    an ``html_url``). Fetch the full :py:class:`Organization` via
    :py:class:`~action0.github.operations.orgs.GetOrg` when needed.
    """

    login: str
    """The organization's login name."""

    id: int
    """The numeric organization id."""

    description: str | None = None
    """The description, if set."""

    @classmethod
    def from_json(cls, data: Any) -> SimpleOrganization:
        """
        Build a membership entry from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the organization entry
        """
        return cls(
            login=data["login"],
            id=data["id"],
            description=data.get("description"),
        )


@dataclass
class Organization:
    """
    A GitHub organization's full profile.

    This is GitHub's ``organization-full`` schema, reduced to the
    commonly used fields. Where an organization appears embedded in
    other payloads (e.g. as a repository owner), GitHub sends a plain
    user object instead — that stays a
    :py:class:`~action0.github.models.user.SimpleUser`.
    """

    login: str
    """The organization's login name, e.g. ``"python"``."""

    id: int
    """The numeric organization id."""

    html_url: str
    """The web URL, e.g. ``"https://github.com/python"``."""

    name: str | None = None
    """The display name, if set."""

    description: str | None = None
    """The description, if set."""

    blog: str | None = None
    """The website URL, if set (GitHub's ``""`` for a cleared field is
    normalized to ``None``)."""

    location: str | None = None
    """The location, if set."""

    public_repos: int = 0
    """The number of public repositories."""

    followers: int = 0
    """The number of followers."""

    created_at: datetime | None = None
    """When the organization was created."""

    @classmethod
    def from_json(cls, data: Any) -> Organization:
        """
        Build an organization from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the organization
        """
        return cls(
            login=data["login"],
            id=data["id"],
            html_url=data["html_url"],
            name=data.get("name"),
            description=data.get("description"),
            blog=data.get("blog") or None,
            location=data.get("location"),
            public_repos=data.get("public_repos", 0),
            followers=data.get("followers", 0),
            created_at=timestamp(data.get("created_at")),
        )
