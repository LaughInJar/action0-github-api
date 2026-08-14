"""The user operations (`GitHub docs <https://docs.github.com/en/rest/users/users>`__)."""

from __future__ import annotations

from typing import Any

from action0.client import path_param
from action0.req import Method

from ..models.user import User
from .base import GitHubOperation


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
