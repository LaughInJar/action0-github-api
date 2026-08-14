import asyncio
import json
import unittest

from action0.client.testing import AsyncStubBackend
from action0.client.testing import DeferredStubBackend
from action0.client.testing import StubBackend
from action0.client.testing import deferred_result
from action0.github import GitHubClient
from action0.github import ListOrgRepos
from action0.github import all_items
from action0.github import all_items_async
from action0.github import all_items_deferred
from action0.req import Response


def _repo(name: str) -> dict[str, object]:
    """
    :param name: the repository name
    :return: a minimal repository payload
    """
    return {
        "id": hash(name) % 1000,
        "name": name,
        "full_name": f"python/{name}",
        "owner": {
            "login": "python",
            "id": 1,
            "html_url": "https://github.com/python",
            "type": "Organization",
        },
        "private": False,
        "html_url": f"https://github.com/python/{name}",
        "default_branch": "main",
    }


NEXT_LINK = '<https://api.github.com/orgs/python/repos?per_page=2&page=2>; rel="next"'

PAGE_1 = Response(
    200, body=json.dumps([_repo("cpython"), _repo("peps")]), headers={"Link": NEXT_LINK}
)
PAGE_2 = Response(200, body=json.dumps([_repo("mypy")]))  # no Link header: the last page


class AllItemsTestCase(unittest.TestCase):
    """
    tests for the :py:mod:`action0.github.pagination` helpers — the same
    two-page listing in the three execution models
    """

    def test_all_items_sync(self) -> None:
        """
        Test that the sync helper yields the items of all pages, fetching
        the second page with the incremented page number.
        """
        backend = StubBackend(PAGE_1, PAGE_2)
        client = GitHubClient(backend)

        names = [repo.name for repo in all_items(client, ListOrgRepos(org="python", per_page=2))]

        self.assertEqual(names, ["cpython", "peps", "mypy"])
        self.assertEqual(
            [request.url.as_str() for request in backend.requests],
            [
                "https://api.github.com/orgs/python/repos?per_page=2&page=1",
                "https://api.github.com/orgs/python/repos?per_page=2&page=2",
            ],
        )

    def test_all_items_is_lazy(self) -> None:
        """
        Test that pages are only fetched as the iteration proceeds.
        """
        backend = StubBackend(PAGE_1, PAGE_2)
        client = GitHubClient(backend)

        iterator = all_items(client, ListOrgRepos(org="python", per_page=2))
        next(iterator)  # first item: only the first page was fetched
        self.assertEqual(len(backend.requests), 1)

        list(iterator)  # exhausting it fetches the rest
        self.assertEqual(len(backend.requests), 2)

    def test_all_items_async(self) -> None:
        """
        Test the async helper — same pages, ``async for`` consumption.
        """
        backend = AsyncStubBackend(PAGE_1, PAGE_2)
        client = GitHubClient(backend)

        async def collect() -> list[str]:
            return [
                repo.name
                async for repo in all_items_async(client, ListOrgRepos(org="python", per_page=2))
            ]

        self.assertEqual(asyncio.run(collect()), ["cpython", "peps", "mypy"])
        self.assertEqual(len(backend.requests), 2)

    def test_all_items_deferred(self) -> None:
        """
        Test the Twisted helper — it gathers all pages into one list.
        """
        backend = DeferredStubBackend(PAGE_1, PAGE_2)
        client = GitHubClient(backend)

        deferred = all_items_deferred(client, ListOrgRepos(org="python", per_page=2))

        self.assertEqual(
            [repo.name for repo in deferred_result(deferred)], ["cpython", "peps", "mypy"]
        )
        self.assertEqual(len(backend.requests), 2)
