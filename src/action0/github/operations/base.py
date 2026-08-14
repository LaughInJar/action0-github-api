"""
The base classes shared by all GitHub operations
(:py:class:`GitHubOperation`, :py:class:`PaginatedOperation`) and the
query vocabularies GitHub uses across resource areas
(:py:class:`SortDirection`).
"""

from abc import abstractmethod
from dataclasses import replace
from enum import StrEnum
from typing import Any
from typing import TypeVar

from action0.client import JsonOperation
from action0.client import query
from action0.req import Response

from ..models.page import ItemT
from ..models.page import Page
from .links import links

R_co = TypeVar("R_co", covariant=True)
"""The parsed result type of a GitHub operation."""

PageT = TypeVar("PageT", bound=Page[Any])
"""A page result — :py:class:`~action0.github.models.page.Page` or a
subclass like :py:class:`~action0.github.models.search.SearchPage`."""


def attach_next(operation: Any, page: PageT, response: Response) -> PageT:
    """
    Attach the next-page operation to a freshly parsed page: a copy of
    the given operation with its ``page`` field incremented — exactly
    when the response's ``Link`` header announces a ``rel="next"``
    (GitHub's authoritative end-of-listing signal).

    ``dataclasses.replace`` keeps the page's concrete type, so subclasses
    like :py:class:`~action0.github.models.search.SearchPage` pass
    through with their extra fields intact.

    :param operation: the operation that produced the page — any
                      operation dataclass with a ``page`` field (typed
                      ``Any``: "has a page field" spans the unrelated
                      :py:class:`PaginatedOperation` and
                      :py:class:`~action0.github.operations.search.SearchOperation`
                      hierarchies)
    :param page: the parsed page, ``next`` not yet set
    :param response: the response it was parsed from
    :return: the page, with ``next`` attached if there is one
    """
    if "next" in links(response):
        return replace(page, next=replace(operation, page=operation.page + 1))
    return page


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


class PaginatedOperation(GitHubOperation[Page[ItemT]]):
    """
    The base class of the listing operations: GitHub's page-number
    pagination as query fields, and the result wrapped as a
    :py:class:`~action0.github.models.page.Page` whose ``next`` is the
    ready-to-send operation for the following page — present exactly when
    the response's ``Link`` header announces a ``rel="next"`` (GitHub's
    authoritative signal), built as a copy of this operation with
    :py:attr:`page` + 1.

    Subclasses implement :py:meth:`load_item` for a single JSON array
    item. Being base-class fields, ``per_page`` and ``page`` come first
    in every listing's query string.
    """

    per_page: int = query(default=30)
    """The page size (GitHub caps it at 100)."""

    page: int = query(default=1)
    """The page number, starting at 1."""

    @abstractmethod
    def load_item(self, data: Any) -> ItemT:
        """
        Turn one item of the decoded JSON array into the typed model.

        :param data: one decoded JSON array item
        :return: the parsed item
        """

    def load_json(self, data: Any) -> Page[ItemT]:
        """
        :param data: the decoded JSON payload (an array)
        :return: the page, without pagination yet (:py:meth:`load` adds
                 it — only the response's ``Link`` header knows)
        """
        return Page(items=[self.load_item(item) for item in data])

    def load(self, response: Response) -> Page[ItemT]:
        """
        Decode the page (via :py:class:`JsonOperation
        <action0.client.operation.JsonOperation>`'s JSON handling) and
        attach the next-page operation if the response's ``Link`` header
        announces one.

        :param response: the response, already vetted
        :return: the page
        """
        return attach_next(self, super().load(response), response)
