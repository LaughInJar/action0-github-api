"""The repository operations (`GitHub docs <https://docs.github.com/en/rest/repos/repos>`__)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from action0.client import json_field
from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.repo import Repo
from ..models.tag import Tag
from ..models.user import Contributor
from .base import GitHubOperation
from .base import PaginatedOperation
from .base import SortDirection

__all__ = [
    "GetRepo",
    "GetRepoTopics",
    "ListContributors",
    "ListLanguages",
    "ListOrgRepos",
    "ListRepoTags",
    "ListUserRepos",
    "OrgRepoType",
    "ReplaceRepoTopics",
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


class _ListRepos(PaginatedOperation[Repo]):
    """
    The shared shape of the repository listings: sorting query fields
    (enums are serialized to their values, ``None`` fields are simply not
    sent) on top of the pagination ones, and pages of repositories as the
    result.
    """

    sort: RepoSort | None = query(default=None)
    """The sort order; ``None`` uses GitHub's default (``created``)."""

    direction: SortDirection | None = query(default=None)
    """The sort direction; GitHub's default is ``asc`` when :py:attr:`sort`
    is ``full_name``, ``desc`` otherwise."""

    def load_item(self, data: Any) -> Repo:
        """
        :param data: one decoded JSON array item
        :return: the repository
        """
        return Repo.from_json(data)


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


class ListRepoTags(PaginatedOperation[Tag]):
    """
    ``GET /repos/{owner}/{repo}/tags`` — list a repository's tags,
    newest first.

    >>> operation = ListRepoTags(owner="python", repo="cpython", per_page=5)
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/cpython/tags?per_page=5&page=1'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/tags"

    owner: str = path_param()
    repo: str = path_param()

    def load_item(self, data: Any) -> Tag:
        """
        :param data: one decoded JSON array item
        :return: the tag
        """
        return Tag.from_json(data)


class ListContributors(PaginatedOperation[Contributor]):
    """
    ``GET /repos/{owner}/{repo}/contributors`` — list who contributed,
    most commits first (each item a
    :py:class:`~action0.github.models.user.Contributor` — a user plus
    their commit count).
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/contributors"

    owner: str = path_param()
    repo: str = path_param()

    def load_item(self, data: Any) -> Contributor:
        """
        :param data: one decoded JSON array item
        :return: the contributor
        """
        return Contributor.from_json(data)


class ListLanguages(GitHubOperation[dict[str, int]]):
    """
    ``GET /repos/{owner}/{repo}/languages`` — the repository's language
    breakdown, handed through as GitHub sends it: language name →
    bytes of code, largest first.

    >>> operation = ListLanguages(owner="python", repo="cpython")
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/cpython/languages'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/languages"

    owner: str = path_param()
    repo: str = path_param()

    def load_json(self, data: Any) -> dict[str, int]:
        """
        :param data: the decoded JSON payload
        :return: language name → bytes of code
        """
        return dict(data)


class GetRepoTopics(GitHubOperation[list[str]]):
    """
    ``GET /repos/{owner}/{repo}/topics`` — the repository's topics, as
    the plain list of names (unwrapped from GitHub's ``{names: [...]}``
    envelope).
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/topics"

    owner: str = path_param()
    repo: str = path_param()

    def load_json(self, data: Any) -> list[str]:
        """
        :param data: the decoded JSON payload (the envelope)
        :return: the topic names
        """
        return list(data["names"])


class ReplaceRepoTopics(GitHubOperation[list[str]]):
    """
    ``PUT /repos/{owner}/{repo}/topics`` — replace the repository's
    topics wholesale (there is no incremental add/remove in GitHub's
    API; read-modify-write via :py:class:`GetRepoTopics`). Requires a
    token with write access; ``[]`` clears them.
    """

    method = Method.PUT
    path = "/repos/{owner}/{repo}/topics"

    owner: str = path_param()
    repo: str = path_param()

    names: list[str] = json_field()
    """The complete new topic set (lowercase letters, digits and
    hyphens — GitHub answers 422 otherwise)."""

    def load_json(self, data: Any) -> list[str]:
        """
        :param data: the decoded JSON payload (the envelope)
        :return: the topic names as stored
        """
        return list(data["names"])
