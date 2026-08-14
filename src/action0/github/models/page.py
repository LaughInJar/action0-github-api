"""One page of a listing result (:py:class:`Page`)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeVar
from typing import overload

from action0.client import Operation

ItemT = TypeVar("ItemT")
"""The item type of a page — e.g. a repository or an issue."""


@dataclass
class Page(Sequence[ItemT]):
    """
    One page of a listing, plus the way to the next one.

    A page behaves like the sequence of its :py:attr:`items` (iteration,
    ``len()``, indexing, truthiness), so code that treats a listing result
    as a list keeps working. :py:attr:`next` carries pagination: the
    ready-to-send operation for the following page, or ``None`` on the
    last one.
    """

    items: list[ItemT]
    """The items of this page."""

    next: Operation[Page[ItemT]] | None = None
    """The operation fetching the next page — send it through the same
    client (in whatever execution model) — or ``None`` if this is the
    last page."""

    @overload
    def __getitem__(self, index: int) -> ItemT: ...

    @overload
    def __getitem__(self, index: slice) -> list[ItemT]: ...

    def __getitem__(self, index: int | slice) -> ItemT | list[ItemT]:
        """
        :param index: an item index or slice
        :return: the item(s) at that position
        """
        return self.items[index]

    def __len__(self) -> int:
        """
        :return: the number of items on this page
        """
        return len(self.items)
