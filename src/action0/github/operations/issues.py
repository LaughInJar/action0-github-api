"""The issue operations (`GitHub docs <https://docs.github.com/en/rest/issues/issues>`__)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from action0.client import json_field
from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.issue import Issue
from .base import GitHubOperation
from .base import PaginatedOperation
from .base import SortDirection


class IssueStateFilter(StrEnum):
    """The state filter of :py:class:`ListIssues` (unlike
    :py:class:`~action0.github.models.issue.IssueState` it knows ``all``)."""

    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


class IssueSort(StrEnum):
    """The sort orders of the issue listing."""

    CREATED = "created"
    UPDATED = "updated"
    COMMENTS = "comments"


class ListIssues(PaginatedOperation[Issue]):
    """
    ``GET /repos/{owner}/{repo}/issues`` — list a repository's issues.

    GitHub returns pull requests here too (every pull request is an
    issue); filter them out via
    :py:attr:`~action0.github.models.issue.Issue.is_pull_request`.

    >>> operation = ListIssues(owner="python", repo="peps", state=IssueStateFilter.CLOSED)
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/peps/issues?per_page=30&page=1&state=closed'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/issues"

    owner: str = path_param()
    repo: str = path_param()

    state: IssueStateFilter | None = query(default=None)
    """The state filter; ``None`` uses GitHub's default (``open``)."""

    labels: str | None = query(default=None)
    """Label names to filter by, comma-separated (``"bug,ui"``) — GitHub's
    own wire format for this parameter."""

    sort: IssueSort | None = query(default=None)
    """The sort order; ``None`` uses GitHub's default (``created``)."""

    direction: SortDirection | None = query(default=None)
    """The sort direction; ``None`` uses GitHub's default (``desc``)."""

    since: datetime | None = query(default=None)
    """Only issues updated at or after this time (serialized to ISO 8601)."""

    def load_item(self, data: Any) -> Issue:
        """
        :param data: one decoded JSON array item
        :return: the issue
        """
        return Issue.from_json(data)


class CreateIssue(GitHubOperation[Issue]):
    """
    ``POST /repos/{owner}/{repo}/issues`` — create an issue.

    The non-path fields become the JSON request body; ``None`` fields are
    omitted from it (requires a token with write access to the repository).
    """

    method = Method.POST
    path = "/repos/{owner}/{repo}/issues"

    owner: str = path_param()
    repo: str = path_param()

    title: str = json_field()
    """The issue title."""

    body: str | None = json_field(default=None)
    """The description text (GitHub-flavored Markdown)."""

    labels: list[str] | None = json_field(default=None)
    """Label names to attach."""

    assignees: list[str] | None = json_field(default=None)
    """Logins to assign."""

    def load_json(self, data: Any) -> Issue:
        """
        :param data: the decoded JSON payload
        :return: the created issue (with its server-assigned number)
        """
        return Issue.from_json(data)
