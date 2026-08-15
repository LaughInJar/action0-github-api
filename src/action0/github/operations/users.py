"""The user operations (`GitHub docs <https://docs.github.com/en/rest/users/users>`__)."""

from __future__ import annotations

from typing import Any

from action0.client import path_param
from action0.req import Method

from ..models.org import SimpleOrganization
from ..models.user import SimpleUser
from ..models.user import User
from .base import GitHubOperation
from .base import PaginatedOperation


class GetUser(GitHubOperation[User]):
    """
    ``GET /users/{username}`` — fetch a user's public profile.

    >>> GetUser(username="gvanrossum").as_request("https://api.github.com").url.as_str()
    'https://api.github.com/users/gvanrossum'
    """

    method = Method.GET
    path = "/users/{username}"

    username: str = path_param()

    def load_json(self, data: Any) -> User:
        """
        :param data: the decoded JSON payload
        :return: the user
        """
        return User.from_json(data)


class GetAuthenticatedUser(GitHubOperation[User]):
    """
    ``GET /user`` — fetch the profile behind the client's token (requires
    one; the response additionally carries private counts the
    :py:class:`~action0.github.models.user.User` model ignores).
    """

    method = Method.GET
    path = "/user"

    def load_json(self, data: Any) -> User:
        """
        :param data: the decoded JSON payload
        :return: the authenticated user
        """
        return User.from_json(data)


class ListFollowers(PaginatedOperation[SimpleUser]):
    """
    ``GET /users/{username}/followers`` — list who follows a user.

    >>> operation = ListFollowers(username="gvanrossum")
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/users/gvanrossum/followers?per_page=30&page=1'
    """

    method = Method.GET
    path = "/users/{username}/followers"

    username: str = path_param()

    def load_item(self, data: Any) -> SimpleUser:
        """
        :param data: one decoded JSON array item
        :return: the follower
        """
        return SimpleUser.from_json(data)


class ListUserOrgs(PaginatedOperation[SimpleOrganization]):
    """
    ``GET /users/{username}/orgs`` — list a user's *public*
    organization memberships. The items are
    :py:class:`~action0.github.models.org.SimpleOrganization` — the
    membership payloads carry no profile fields, so follow up with
    :py:class:`~action0.github.operations.orgs.GetOrg` for the full
    :py:class:`~action0.github.models.org.Organization`.
    """

    method = Method.GET
    path = "/users/{username}/orgs"

    username: str = path_param()

    def load_item(self, data: Any) -> SimpleOrganization:
        """
        :param data: one decoded JSON array item
        :return: the organization membership entry
        """
        return SimpleOrganization.from_json(data)
