"""The pull request review operations
(`GitHub docs <https://docs.github.com/en/rest/pulls/reviews>`__)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from action0.client import json_field
from action0.client import path_param
from action0.client import query
from action0.req import Method

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
