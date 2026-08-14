"""The search operations (`GitHub docs <https://docs.github.com/en/rest/search/search>`__)."""

from __future__ import annotations

from abc import abstractmethod
from enum import StrEnum
from typing import Any

from action0.client import query
from action0.req import Method
from action0.req import Response

from ..models.page import ItemT
from ..models.repo import Repo
from ..models.search import SearchPage
from .base import GitHubOperation
from .base import SortDirection
from .base import attach_next


class RepoSearchSort(StrEnum):
    """The sort orders of the repository search (``None`` = best match)."""

    STARS = "stars"
    FORKS = "forks"
    HELP_WANTED_ISSUES = "help-wanted-issues"
    UPDATED = "updated"


class SearchOperation(GitHubOperation[SearchPage[ItemT]]):
    """
    The base class of the search operations: GitHub wraps search results
    in a ``{total_count, incomplete_results, items}`` envelope instead of
    a bare array, parsed into a
    :py:class:`~action0.github.models.search.SearchPage`.

    Subclasses implement :py:meth:`load_item` for one ``items`` entry.
    """

    # the same pagination fields as PaginatedOperation — declared again
    # because one operation class cannot be generic over both Page[ItemT]
    # and SearchPage[ItemT] (Python has no higher-kinded types); the
    # Link-header pagination logic itself is shared via attach_next
    per_page: int = query(default=30)
    """The page size (GitHub caps it at 100)."""

    page: int = query(default=1)
    """The page number, starting at 1."""

    @abstractmethod
    def load_item(self, data: Any) -> ItemT:
        """
        Turn one entry of the envelope's ``items`` array into the typed
        model.

        :param data: one decoded ``items`` entry
        :return: the parsed item
        """

    def load_json(self, data: Any) -> SearchPage[ItemT]:
        """
        :param data: the decoded JSON payload (the search envelope)
        :return: the search page, without pagination yet (:py:meth:`load`
                 adds it — only the response's ``Link`` header knows)
        """
        return SearchPage(
            items=[self.load_item(item) for item in data["items"]],
            total_count=data["total_count"],
            incomplete_results=data.get("incomplete_results", False),
        )

    def load(self, response: Response) -> SearchPage[ItemT]:
        """
        Decode the envelope and attach the next-page operation if the
        response's ``Link`` header announces one.

        :param response: the response, already vetted
        :return: the search page
        """
        return attach_next(self, super().load(response), response)


class SearchRepos(SearchOperation[Repo]):
    """
    ``GET /search/repositories`` — search repositories with GitHub's
    `query syntax
    <https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories>`__.

    >>> operation = SearchRepos(q="http client language:python", sort=RepoSearchSort.STARS)
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/search/repositories?per_page=30&page=1&q=http+client+language%3Apython&sort=stars'
    """

    method = Method.GET
    path = "/search/repositories"

    q: str = query()
    """The search query, e.g. ``"http client language:python stars:>100"``."""

    sort: RepoSearchSort | None = query(default=None)
    """The sort order; ``None`` uses GitHub's default (best match)."""

    order: SortDirection | None = query(default=None)
    """The sort direction (GitHub's parameter name for search); only
    applied when :py:attr:`sort` is set, default ``desc``."""

    def load_item(self, data: Any) -> Repo:
        """
        :param data: one decoded ``items`` entry
        :return: the repository
        """
        return Repo.from_json(data)
