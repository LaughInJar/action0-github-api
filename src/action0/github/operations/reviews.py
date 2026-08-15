"""The pull request review operations
(`GitHub docs <https://docs.github.com/en/rest/pulls/reviews>`__)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from action0.client import json_field
from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.pull import PullRequest
from ..models.review import Review
from ..models.review import ReviewComment
from .base import GitHubOperation
from .base import PaginatedOperation


class ReviewEvent(StrEnum):
    """The verdict submitted with :py:class:`CreatePullReview` —
    uppercase on the wire, like the review states."""

    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    COMMENT = "COMMENT"


class ReviewSide(StrEnum):
    """Which side of the diff a review comment anchors to."""

    LEFT = "LEFT"
    RIGHT = "RIGHT"


@dataclass
class DraftReviewComment:
    """
    One line comment submitted *inside* a :py:class:`CreatePullReview`
    batch — a plain dataclass that becomes one entry of the review's
    ``comments`` array (``None`` fields are omitted, as everywhere).
    For a standalone comment outside a review, use
    :py:class:`CreateReviewComment`.
    """

    path: str
    """The file the comment anchors to."""

    body: str
    """The comment text (GitHub-flavored Markdown)."""

    line: int
    """The line in the diff (the last line, for a multi-line
    comment)."""

    side: ReviewSide | None = None
    """Which side of the diff; ``None`` uses GitHub's default
    (``RIGHT`` — the new code)."""

    start_line: int | None = None
    """The first line, to span a multi-line range; ``None`` comments a
    single line."""

    start_side: ReviewSide | None = None
    """The side of :py:attr:`start_line`; ``None`` uses GitHub's
    default."""


class ListPullReviews(PaginatedOperation[Review]):
    """
    ``GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews`` — list a
    pull request's reviews, in chronological order.

    >>> operation = ListPullReviews(owner="python", repo="peps", pull_number=42)
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/peps/pulls/42/reviews?per_page=30&page=1'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/pulls/{pull_number}/reviews"

    owner: str = path_param()
    repo: str = path_param()
    pull_number: int = path_param()

    def load_item(self, data: Any) -> Review:
        """
        :param data: one decoded JSON array item
        :return: the review
        """
        return Review.from_json(data)


class CreatePullReview(GitHubOperation[Review]):
    """
    ``POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews`` — review
    a pull request: approve it, request changes or leave a summary
    comment (requires a token with write access; GitHub refuses
    approving your own pull request).

    This is the plain review flow — submitting line comments in a batch
    is a separate, heavier payload this client does not model.
    """

    method = Method.POST
    path = "/repos/{owner}/{repo}/pulls/{pull_number}/reviews"

    owner: str = path_param()
    repo: str = path_param()
    pull_number: int = path_param()

    event: ReviewEvent = json_field()
    """The verdict. (Omitting it would create a ``PENDING`` draft
    review — this client always submits.)"""

    body: str | None = json_field(default=None)
    """The summary text — required by GitHub for
    :py:attr:`~ReviewEvent.REQUEST_CHANGES` and
    :py:attr:`~ReviewEvent.COMMENT`, optional for an approval."""

    commit_id: str | None = json_field(default=None)
    """The commit the review refers to; ``None`` uses the pull
    request's current head (and risks reviewing code pushed while you
    were reading)."""

    comments: list[DraftReviewComment] | None = json_field(default=None)
    """Line comments to submit with the review, as
    :py:class:`DraftReviewComment` entries — serialized straight into
    GitHub's ``comments`` array."""

    def load_json(self, data: Any) -> Review:
        """
        :param data: the decoded JSON payload
        :return: the created review
        """
        return Review.from_json(data)


class ListReviewComments(PaginatedOperation[ReviewComment]):
    """
    ``GET /repos/{owner}/{repo}/pulls/{pull_number}/comments`` — list a
    pull request's *review* comments (the ones anchored to diff lines).
    The conversation thread lives on the issue side — that is
    :py:class:`~action0.github.operations.issues.ListIssueComments`.
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/pulls/{pull_number}/comments"

    owner: str = path_param()
    repo: str = path_param()
    pull_number: int = path_param()

    since: datetime | None = query(default=None)
    """Only comments updated at or after this time (serialized to
    ISO 8601)."""

    def load_item(self, data: Any) -> ReviewComment:
        """
        :param data: one decoded JSON array item
        :return: the review comment
        """
        return ReviewComment.from_json(data)


class CreateReviewComment(GitHubOperation[ReviewComment]):
    """
    ``POST /repos/{owner}/{repo}/pulls/{pull_number}/comments`` — leave
    one standalone line comment on a pull request's diff (requires a
    token with write access). For several at once, batch them into a
    review via :py:class:`CreatePullReview`'s ``comments``.
    """

    method = Method.POST
    path = "/repos/{owner}/{repo}/pulls/{pull_number}/comments"

    owner: str = path_param()
    repo: str = path_param()
    pull_number: int = path_param()

    body: str = json_field()
    """The comment text (GitHub-flavored Markdown)."""

    commit_id: str = json_field()
    """The sha the comment refers to — the pull request's head sha
    (:py:attr:`pull.head.sha
    <action0.github.models.pull.PullRequestRef.sha>`), *not* the merge
    commit."""

    file_path: str = json_field("path")
    """The file to anchor to (sent as ``path`` — aliased like
    everywhere the name would shadow the path template)."""

    line: int = json_field()
    """The line in the diff (the last line, for a multi-line
    comment)."""

    side: ReviewSide | None = json_field(default=None)
    """Which side of the diff; ``None`` uses GitHub's default
    (``RIGHT`` — the new code)."""

    start_line: int | None = json_field(default=None)
    """The first line, to span a multi-line range; ``None`` comments a
    single line."""

    start_side: ReviewSide | None = json_field(default=None)
    """The side of :py:attr:`start_line`; ``None`` uses GitHub's
    default."""

    def load_json(self, data: Any) -> ReviewComment:
        """
        :param data: the decoded JSON payload
        :return: the created comment (with its server-assigned id)
        """
        return ReviewComment.from_json(data)


class RequestReviewers(GitHubOperation[PullRequest]):
    """
    ``POST /repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers``
    — ask users (and/or teams) for a review. GitHub requires at least
    one of the two lists, refuses the pull request's own author, and
    answers 422 for non-collaborators.
    """

    method = Method.POST
    path = "/repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers"

    owner: str = path_param()
    repo: str = path_param()
    pull_number: int = path_param()

    reviewers: list[str] | None = json_field(default=None)
    """The logins to request."""

    team_reviewers: list[str] | None = json_field(default=None)
    """The team slugs to request (organization repositories only)."""

    def load_json(self, data: Any) -> PullRequest:
        """
        :param data: the decoded JSON payload
        :return: the pull request with its updated
                 ``requested_reviewers``
        """
        return PullRequest.from_json(data)


class RemoveRequestedReviewers(GitHubOperation[PullRequest]):
    """
    ``DELETE /repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers``
    — withdraw review requests (a DELETE with a JSON body, like
    :py:class:`~action0.github.operations.issues.RemoveAssignees`).
    """

    method = Method.DELETE
    path = "/repos/{owner}/{repo}/pulls/{pull_number}/requested_reviewers"

    owner: str = path_param()
    repo: str = path_param()
    pull_number: int = path_param()

    reviewers: list[str] = json_field()
    """The logins whose request to withdraw."""

    team_reviewers: list[str] | None = json_field(default=None)
    """The team slugs whose request to withdraw."""

    def load_json(self, data: Any) -> PullRequest:
        """
        :param data: the decoded JSON payload
        :return: the pull request with its updated
                 ``requested_reviewers``
        """
        return PullRequest.from_json(data)
