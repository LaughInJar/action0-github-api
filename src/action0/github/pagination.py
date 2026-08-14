"""
Iterating over all pages of a listing.

Pagination itself is execution-model-agnostic data: every listing returns
a :py:class:`~action0.github.models.page.Page` whose ``next`` is the
ready-to-send operation for the following page. The helpers here are the
flattening sugar on top — one per execution model, like action0-client's
retry wrappers, because "loop over pages" is spelled differently in sync,
async and Twisted code.

Each helper keeps sending ``page.next`` through the client until the last
page; one GitHub request per page, so mind the rate limit on large
listings (cap via ``per_page``/starting ``page`` if needed).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from collections.abc import Awaitable
from collections.abc import Iterator
from typing import TYPE_CHECKING
from typing import cast

from action0.client import APIClient
from action0.client import Backend
from action0.client import Operation
from action0.req import Response

from .models.page import ItemT
from .models.page import Page

if TYPE_CHECKING:
    # twisted is an optional dependency: only the type checker sees this
    from twisted.internet.defer import Deferred


def all_items(
    client: APIClient[Backend[Response]],
    operation: Operation[Page[ItemT]],
) -> Iterator[ItemT]:
    """
    Iterate over all items of a listing, lazily following the pages
    (sync backends).

    :param client: the client to send through (any sync backend)
    :param operation: the first page's operation
    :return: the items, page by page — each page is fetched only when
             the iteration reaches it
    """
    page = client.send(operation)
    while True:
        yield from page
        if page.next is None:
            return
        page = client.send(page.next)


async def all_items_async(
    client: APIClient[Backend[Awaitable[Response]]],
    operation: Operation[Page[ItemT]],
) -> AsyncIterator[ItemT]:
    """
    Iterate over all items of a listing, lazily following the pages
    (async backends) — consume with ``async for``.

    :param client: the client to send through (any async backend)
    :param operation: the first page's operation
    :return: the items, page by page — each page is fetched only when
             the iteration reaches it
    """
    page = await client.send(operation)
    while True:
        for item in page:
            yield item
        if page.next is None:
            return
        page = await client.send(page.next)


def all_items_deferred(
    client: APIClient[Backend[Deferred[Response]]],
    operation: Operation[Page[ItemT]],
) -> Deferred[list[ItemT]]:
    """
    Collect all items of a listing, following the pages (Twisted
    backends). Unlike the sync/async helpers this gathers everything into
    one list — a Deferred cannot stream lazily.

    :param client: the client to send through (a Twisted backend)
    :param operation: the first page's operation
    :return: a Deferred firing with the items of all pages
    """
    items: list[ItemT] = []

    def collect(page: Page[ItemT]) -> object:
        # returning a Deferred from a callback chains it: the outer
        # Deferred fires only once the whole page chain is done
        items.extend(page.items)
        if page.next is None:
            return items
        return client.send(page.next).addCallback(collect)

    chained: Deferred[object] = client.send(operation).addCallback(collect)
    # Deferred chaining unwraps the callback's Deferreds at runtime, so
    # this fires with the item list — inexpressible in twisted's stubs
    return cast("Deferred[list[ItemT]]", chained)
