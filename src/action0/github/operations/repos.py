"""The repository operations (`GitHub docs <https://docs.github.com/en/rest/repos/repos>`__)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.repo import Repo
from .base import GitHubOperation
from .base import PaginatedOperation
from .base import SortDirection

__all__ = [
    "GetRepo",
    "ListOrgRepos",
    "ListUserRepos",
    "OrgRepoType",
    "RepoSort",
    "SortDirection",  # re-exported: it moved to .base when the issues listings arrived
    "UserRepoType",
]


class RepoSort(StrEnum):
    """The sort orders of the repository listings."""

    CREATED = "created"
    UPDATED = "updated"
    PUSHED = "pushed"
    FULL_NAME = "full_name"


class OrgRepoType(StrEnum):
    """The repository-type filter of :py:class:`ListOrgRepos`."""

    ALL = "all"
    PUBLIC = "public"
    PRIVATE = "private"
    FORKS = "forks"
    SOURCES = "sources"
    MEMBER = "member"


class UserRepoType(StrEnum):
    """The repository-type filter of :py:class:`ListUserRepos`."""

    ALL = "all"
    OWNER = "owner"
    MEMBER = "member"


class GetRepo(GitHubOperation[Repo]):
    """
    ``GET /repos/{owner}/{repo}`` — fetch one repository.

    >>> GetRepo(owner="python", repo="cpython").as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/cpython'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}"

    owner: str = path_param()
    repo: str = path_param()

    def load_json(self, data: Any) -> Repo:
        """
        :param data: the decoded JSON payload
        :return: the repository
        """
        return Repo.from_json(data)


class _ListRepos(PaginatedOperation[list[Repo]]):
    """
    The shared shape of the repository listings: sorting query fields
    (enums are serialized to their values, ``None`` fields are simply not
    sent) on top of the pagination ones, and the JSON-array-of-repos
    parsing.
    """

    sort: RepoSort | None = query(default=None)
    """The sort order; ``None`` uses GitHub's default (``created``)."""

    direction: SortDirection | None = query(default=None)
    """The sort direction; GitHub's default is ``asc`` when :py:attr:`sort`
    is ``full_name``, ``desc`` otherwise."""

    def load_json(self, data: Any) -> list[Repo]:
        """
        :param data: the decoded JSON payload (an array of repositories)
        :return: the repositories of the requested page
        """
        return [Repo.from_json(item) for item in data]


class ListOrgRepos(_ListRepos):
    """
    ``GET /orgs/{org}/repos`` — list an organization's repositories.

    >>> operation = ListOrgRepos(org="python", sort=RepoSort.PUSHED, per_page=5)
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/orgs/python/repos?per_page=5&page=1&sort=pushed'
    """

    method = Method.GET
    path = "/orgs/{org}/repos"

    org: str = path_param()
    type: OrgRepoType | None = query(default=None)
    """The repository-type filter; ``None`` uses GitHub's default (``all``)."""


class ListUserRepos(_ListRepos):
    """``GET /users/{username}/repos`` — list a user's repositories."""

    method = Method.GET
    path = "/users/{username}/repos"

    username: str = path_param()
    type: UserRepoType | None = query(default=None)
    """The repository-type filter; ``None`` uses GitHub's default (``owner``)."""
