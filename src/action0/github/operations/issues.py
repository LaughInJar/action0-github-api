"""The issue operations (`GitHub docs <https://docs.github.com/en/rest/issues/issues>`__)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from action0.client import json_field
from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.comment import IssueComment
from ..models.issue import Issue
from ..models.issue import IssueState
from .base import GitHubOperation
from .base import NoContentOperation
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


class IssueStateReason(StrEnum):
    """The reason attached to an issue's state by :py:class:`UpdateIssue`."""

    COMPLETED = "completed"
    NOT_PLANNED = "not_planned"
    REOPENED = "reopened"


class LockReason(StrEnum):
    """The reason :py:class:`LockIssue` attaches to a locked
    conversation (note ``"too heated"`` — GitHub's value contains a
    space)."""

    OFF_TOPIC = "off-topic"
    TOO_HEATED = "too heated"
    RESOLVED = "resolved"
    SPAM = "spam"


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


class GetIssue(GitHubOperation[Issue]):
    """
    ``GET /repos/{owner}/{repo}/issues/{issue_number}`` — fetch one
    issue (or pull request — see
    :py:attr:`~action0.github.models.issue.Issue.is_pull_request`).

    >>> operation = GetIssue(owner="python", repo="peps", issue_number=42)
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/peps/issues/42'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/issues/{issue_number}"

    owner: str = path_param()
    repo: str = path_param()
    issue_number: int = path_param()

    def load_json(self, data: Any) -> Issue:
        """
        :param data: the decoded JSON payload
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


class UpdateIssue(GitHubOperation[Issue]):
    """
    ``PATCH /repos/{owner}/{repo}/issues/{issue_number}`` — update an
    issue (requires a token with write access to the repository).

    PATCH semantics: only the fields you set are changed — a ``None``
    field is omitted from the JSON body and leaves the issue untouched.
    (This also means clearing a field by sending JSON ``null`` is not
    expressible here; send an empty string/list instead where GitHub
    accepts one.) Like every non-idempotent method, a PATCH is never
    blindly repeated by
    :py:class:`~action0.github.retry.GitHubRetryPolicy`.
    """

    method = Method.PATCH
    path = "/repos/{owner}/{repo}/issues/{issue_number}"

    owner: str = path_param()
    repo: str = path_param()
    issue_number: int = path_param()

    title: str | None = json_field(default=None)
    """The new title."""

    body: str | None = json_field(default=None)
    """The new description text (GitHub-flavored Markdown)."""

    state: IssueState | None = json_field(default=None)
    """Open or close the issue."""

    state_reason: IssueStateReason | None = json_field(default=None)
    """The reason to attach to the state change (close as
    ``completed``/``not_planned``, reopen as ``reopened``)."""

    labels: list[str] | None = json_field(default=None)
    """The new label names — replaces the whole set (``[]`` clears it)."""

    assignees: list[str] | None = json_field(default=None)
    """The new assignee logins — replaces the whole set (``[]`` clears
    it)."""

    def load_json(self, data: Any) -> Issue:
        """
        :param data: the decoded JSON payload
        :return: the updated issue
        """
        return Issue.from_json(data)


class ListIssueComments(PaginatedOperation[IssueComment]):
    """
    ``GET /repos/{owner}/{repo}/issues/{issue_number}/comments`` — list
    an issue's comments, oldest first (pull request conversation
    comments live here too — every pull request is an issue).

    >>> operation = ListIssueComments(owner="python", repo="peps", issue_number=42)
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/peps/issues/42/comments?per_page=30&page=1'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/issues/{issue_number}/comments"

    owner: str = path_param()
    repo: str = path_param()
    issue_number: int = path_param()

    since: datetime | None = query(default=None)
    """Only comments updated at or after this time (serialized to
    ISO 8601)."""

    def load_item(self, data: Any) -> IssueComment:
        """
        :param data: one decoded JSON array item
        :return: the comment
        """
        return IssueComment.from_json(data)


class CreateIssueComment(GitHubOperation[IssueComment]):
    """
    ``POST /repos/{owner}/{repo}/issues/{issue_number}/comments`` —
    comment on an issue or pull request (requires a token with write
    access to the repository).
    """

    method = Method.POST
    path = "/repos/{owner}/{repo}/issues/{issue_number}/comments"

    owner: str = path_param()
    repo: str = path_param()
    issue_number: int = path_param()

    body: str = json_field()
    """The comment text (GitHub-flavored Markdown)."""

    def load_json(self, data: Any) -> IssueComment:
        """
        :param data: the decoded JSON payload
        :return: the created comment (with its server-assigned id)
        """
        return IssueComment.from_json(data)


class UpdateIssueComment(GitHubOperation[IssueComment]):
    """
    ``PATCH /repos/{owner}/{repo}/issues/comments/{comment_id}`` — edit
    a comment. Note the address: comment ids are repository-global, so
    no issue number appears in the path.
    """

    method = Method.PATCH
    path = "/repos/{owner}/{repo}/issues/comments/{comment_id}"

    owner: str = path_param()
    repo: str = path_param()

    comment_id: int = path_param()
    """The comment id (:py:attr:`IssueComment.id
    <action0.github.models.comment.IssueComment.id>`) — *not* the issue
    number."""

    body: str = json_field()
    """The new comment text — replaces the old one entirely."""

    def load_json(self, data: Any) -> IssueComment:
        """
        :param data: the decoded JSON payload
        :return: the updated comment
        """
        return IssueComment.from_json(data)


class DeleteIssueComment(NoContentOperation):
    """
    ``DELETE /repos/{owner}/{repo}/issues/comments/{comment_id}`` —
    delete a comment, for good. The first no-content operation: GitHub
    answers ``204``, ``send`` yields ``None``.

    >>> operation = DeleteIssueComment(owner="octo", repo="demo", comment_id=1)
    >>> request = operation.as_request("https://api.github.com")
    >>> f"{request.method} {request.url.as_str()}"
    'DELETE https://api.github.com/repos/octo/demo/issues/comments/1'
    """

    method = Method.DELETE
    path = "/repos/{owner}/{repo}/issues/comments/{comment_id}"

    owner: str = path_param()
    repo: str = path_param()

    comment_id: int = path_param()
    """The comment id — *not* the issue number."""


class LockIssue(NoContentOperation):
    """
    ``PUT /repos/{owner}/{repo}/issues/{issue_number}/lock`` — lock an
    issue's (or pull request's) conversation: only collaborators can
    comment until it is unlocked. Answers ``204``.
    """

    method = Method.PUT
    path = "/repos/{owner}/{repo}/issues/{issue_number}/lock"

    owner: str = path_param()
    repo: str = path_param()
    issue_number: int = path_param()

    lock_reason: LockReason | None = json_field(default=None)
    """The reason shown in the timeline; ``None`` locks without one."""


class UnlockIssue(NoContentOperation):
    """
    ``DELETE /repos/{owner}/{repo}/issues/{issue_number}/lock`` —
    unlock the conversation again. Answers ``204``.
    """

    method = Method.DELETE
    path = "/repos/{owner}/{repo}/issues/{issue_number}/lock"

    owner: str = path_param()
    repo: str = path_param()
    issue_number: int = path_param()


class AddAssignees(GitHubOperation[Issue]):
    """
    ``POST /repos/{owner}/{repo}/issues/{issue_number}/assignees`` —
    add assignees to an issue or pull request, keeping the existing
    ones (unlike :py:class:`UpdateIssue`'s ``assignees``, which
    replaces the whole set). Unassignable logins are silently ignored
    by GitHub.
    """

    method = Method.POST
    path = "/repos/{owner}/{repo}/issues/{issue_number}/assignees"

    owner: str = path_param()
    repo: str = path_param()
    issue_number: int = path_param()

    assignees: list[str] = json_field()
    """The logins to add (at most 10 assignees in total)."""

    def load_json(self, data: Any) -> Issue:
        """
        :param data: the decoded JSON payload
        :return: the issue with its updated assignee set
        """
        return Issue.from_json(data)


class RemoveAssignees(GitHubOperation[Issue]):
    """
    ``DELETE /repos/{owner}/{repo}/issues/{issue_number}/assignees`` —
    remove assignees from an issue or pull request. A DELETE carrying a
    JSON body — GitHub's design, unusual but valid HTTP; the fields
    serialize exactly like every other body.
    """

    method = Method.DELETE
    path = "/repos/{owner}/{repo}/issues/{issue_number}/assignees"

    owner: str = path_param()
    repo: str = path_param()
    issue_number: int = path_param()

    assignees: list[str] = json_field()
    """The logins to remove (others stay assigned)."""

    def load_json(self, data: Any) -> Issue:
        """
        :param data: the decoded JSON payload
        :return: the issue with its updated assignee set
        """
        return Issue.from_json(data)
