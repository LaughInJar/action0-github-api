"""One page of a search result (:py:class:`SearchPage`)."""

from __future__ import annotations

from dataclasses import dataclass

# the inherited `next` field's annotation ("Operation[Page[ItemT]] | None")
# is resolved in this module's namespace when the docs are built — keep
# Operation importable here
from action0.client import Operation  # noqa: F401

from .page import ItemT
from .page import Page


@dataclass
class SearchPage(Page[ItemT]):
    """
    One page of a search result: a :py:class:`~action0.github.models.page.Page`
    (sequence-like, ``next`` carries pagination) plus the envelope fields
    GitHub wraps search results in.

    Note that GitHub caps search results at 1000 items — following
    ``next`` simply ends there, whatever :py:attr:`total_count` says.
    """

    total_count: int = 0
    """How many results matched in total (across all pages)."""

    incomplete_results: bool = False
    """Whether GitHub timed out and returned only a partial match set."""
