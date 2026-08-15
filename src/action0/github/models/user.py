"""The user models: :py:class:`SimpleUser` (as GitHub embeds it in other
resources), the full :py:class:`User` profile and the
:py:class:`Contributor` variant."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .timestamps import timestamp


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


@dataclass
class Contributor(SimpleUser):
    """
    A repository contributor — a :py:class:`SimpleUser` plus their
    commit count, as
    :py:class:`~action0.github.operations.repos.ListContributors`
    returns it.
    """

    contributions: int = 0
    """The number of commits to the repository."""

    @classmethod
    def from_json(cls, data: Any) -> Contributor:
        """
        Build a contributor from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the contributor
        """
        return cls(
            login=data["login"],
            id=data["id"],
            html_url=data["html_url"],
            type=data["type"],
            contributions=data.get("contributions", 0),
        )


@dataclass
class User(SimpleUser):
    """
    A full user (or organization) profile, as the user endpoints return
    it: the :py:class:`SimpleUser` core plus the public profile fields.

    This is GitHub's ``public-user`` schema, reduced to the commonly used
    fields (for the authenticated user, GitHub sends additional private
    fields the model ignores).
    """

    name: str | None = None
    """The display name, if set."""

    company: str | None = None
    """The company, if set."""

    blog: str | None = None
    """The blog / website URL, if set."""

    location: str | None = None
    """The location, if set."""

    email: str | None = None
    """The public email address, if set."""

    bio: str | None = None
    """The profile bio, if set."""

    public_repos: int = 0
    """The number of public repositories."""

    public_gists: int = 0
    """The number of public gists."""

    followers: int = 0
    """The number of followers."""

    following: int = 0
    """The number of followed users."""

    created_at: datetime | None = None
    """When the account was created."""

    updated_at: datetime | None = None
    """When the profile was last updated."""

    @classmethod
    def from_json(cls, data: Any) -> User:
        """
        Build a full user profile from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the user
        """
        # GitHub sends "" for a cleared blog field — normalize to None
        blog = data.get("blog") or None
        return cls(
            login=data["login"],
            id=data["id"],
            html_url=data["html_url"],
            type=data["type"],
            name=data.get("name"),
            company=data.get("company"),
            blog=blog,
            location=data.get("location"),
            email=data.get("email"),
            bio=data.get("bio"),
            public_repos=data.get("public_repos", 0),
            public_gists=data.get("public_gists", 0),
            followers=data.get("followers", 0),
            following=data.get("following", 0),
            created_at=timestamp(data.get("created_at")),
            updated_at=timestamp(data.get("updated_at")),
        )
