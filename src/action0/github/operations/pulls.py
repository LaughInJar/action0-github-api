"""The pull request operations (`GitHub docs <https://docs.github.com/en/rest/pulls/pulls>`__)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from action0.client import json_field
from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.pull import PullRequest
from .base import GitHubOperation
from .base import PaginatedOperation
from .base import SortDirection


class PullStateFilter(StrEnum):
    """The state filter of :py:class:`ListPulls` (unlike
    :py:class:`~action0.github.models.issue.IssueState` it knows ``all``)."""

    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


class PullSort(StrEnum):
    """The sort orders of the pull request listing."""

    CREATED = "created"
    UPDATED = "updated"
    POPULARITY = "popularity"
    LONG_RUNNING = "long-running"


class ListPulls(PaginatedOperation[PullRequest]):
    """
    ``GET /repos/{owner}/{repo}/pulls`` — list a repository's pull
    requests.

    >>> operation = ListPulls(owner="python", repo="peps", state=PullStateFilter.CLOSED)
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/peps/pulls?per_page=30&page=1&state=closed'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/pulls"

    owner: str = path_param()
    repo: str = path_param()

    state: PullStateFilter | None = query(default=None)
    """The state filter; ``None`` uses GitHub's default (``open``)."""

    head: str | None = query(default=None)
    """Only pull requests from this head, as ``"owner:branch"``
    (e.g. ``"octocat:new-topic"``)."""

    base: str | None = query(default=None)
    """Only pull requests targeting this base branch name
    (e.g. ``"main"``)."""

    sort: PullSort | None = query(default=None)
    """The sort order; ``None`` uses GitHub's default (``created``)."""

    direction: SortDirection | None = query(default=None)
    """The sort direction; ``None`` uses GitHub's default (``desc``
    when sorting by ``created``, ``asc`` otherwise)."""

    def load_item(self, data: Any) -> PullRequest:
        """
        :param data: one decoded JSON array item
        :return: the pull request
        """
        return PullRequest.from_json(data)


class GetPull(GitHubOperation[PullRequest]):
    """
    ``GET /repos/{owner}/{repo}/pulls/{pull_number}`` — fetch one pull
    request, including the merge/diff statistics the listings omit
    (:py:attr:`~action0.github.models.pull.PullRequest.mergeable`,
    :py:attr:`~action0.github.models.pull.PullRequest.commits`, …).

    >>> operation = GetPull(owner="python", repo="peps", pull_number=42)
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/peps/pulls/42'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/pulls/{pull_number}"

    owner: str = path_param()
    repo: str = path_param()
    pull_number: int = path_param()

    def load_json(self, data: Any) -> PullRequest:
        """
        :param data: the decoded JSON payload
        :return: the pull request
        """
        return PullRequest.from_json(data)


class CreatePull(GitHubOperation[PullRequest]):
    """
    ``POST /repos/{owner}/{repo}/pulls`` — open a pull request.

    The non-path fields become the JSON request body; ``None`` fields
    are omitted from it (requires a token with write access to the
    repository).
    """

    method = Method.POST
    path = "/repos/{owner}/{repo}/pulls"

    owner: str = path_param()
    repo: str = path_param()

    title: str = json_field()
    """The pull request title."""

    head: str = json_field()
    """The branch with the changes — a plain branch name, or
    ``"owner:branch"`` for a cross-repository (fork) pull request."""

    base: str = json_field()
    """The branch the changes should be merged into (in the
    ``{owner}/{repo}`` repository), e.g. ``"main"``."""

    body: str | None = json_field(default=None)
    """The description text (GitHub-flavored Markdown)."""

    draft: bool | None = json_field(default=None)
    """Open as a draft pull request; ``None`` uses GitHub's default
    (``False``)."""

    def load_json(self, data: Any) -> PullRequest:
        """
        :param data: the decoded JSON payload
        :return: the created pull request (with its server-assigned
                 number)
        """
        return PullRequest.from_json(data)
