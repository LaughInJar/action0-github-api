"""
The base classes shared by all GitHub operations
(:py:class:`GitHubOperation`, :py:class:`PaginatedOperation`) and the
query vocabularies GitHub uses across resource areas
(:py:class:`SortDirection`).
"""

from enum import StrEnum
from typing import TypeVar

from action0.client import JsonOperation
from action0.client import query

R_co = TypeVar("R_co", covariant=True)
"""The parsed result type of a GitHub operation."""


class SortDirection(StrEnum):
    """The sort direction of a listing."""

    ASC = "asc"
    DESC = "desc"


class GitHubOperation(JsonOperation[R_co]):
    """
    The base class of all GitHub operations: a
    :py:class:`~action0.client.operation.JsonOperation` requesting GitHub's
    recommended media type.

    ``accept`` lives here (not only as a client default header) because
    :py:meth:`~action0.client.operation.Operation.as_request` sets the
    operation's ``Accept`` before the client's gap-filling defaults run —
    ``JsonOperation``'s plain ``application/json`` would win otherwise.
    """

    accept = "application/vnd.github+json"


class PaginatedOperation(GitHubOperation[R_co]):
    """
    The base class of the listing operations: GitHub's page-number
    pagination as query fields. Pagination is manual for now — pass
    ``page=2`` etc. (a paginator following the ``Link`` header is on the
    roadmap).

    Being base-class fields, ``per_page`` and ``page`` come first in every
    listing's query string.
    """

    per_page: int = query(default=30)
    """The page size (GitHub caps it at 100)."""

    page: int = query(default=1)
    """The page number, starting at 1."""
