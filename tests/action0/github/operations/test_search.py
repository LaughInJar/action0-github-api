import json
import unittest

from action0.client.testing import StubBackend
from action0.github import GitHubClient
from action0.github import RepoSearchSort
from action0.github import SearchPage
from action0.github import SearchRepos
from action0.github import SortDirection
from action0.github import all_items
from action0.req import Response

REPO_PAYLOAD = {
    "id": 81598961,
    "name": "cpython",
    "full_name": "python/cpython",
    "owner": {
        "login": "python",
        "id": 1525981,
        "html_url": "https://github.com/python",
        "type": "Organization",
    },
    "private": False,
    "html_url": "https://github.com/python/cpython",
    "default_branch": "main",
}


def _envelope(*names: str, total: int) -> str:
    """
    :param names: the repository names on this page
    :param total: the envelope's total_count
    :return: a search response body
    """
    items = [dict(REPO_PAYLOAD, name=name, full_name=f"python/{name}") for name in names]
    return json.dumps({"total_count": total, "incomplete_results": False, "items": items})


class SearchReposTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.search.SearchRepos`
    """

    def test_request(self) -> None:
        """
        Test the request shape: the query string q is URL-encoded, the
        enums serialize to their wire values, ``None`` filters are
        omitted (search says ``order``, not ``direction``).
        """
        request = SearchRepos(
            q="http client language:python",
            sort=RepoSearchSort.STARS,
            order=SortDirection.DESC,
        ).as_request("https://api.github.com")

        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/search/repositories"
            "?per_page=30&page=1&q=http+client+language%3Apython&sort=stars&order=desc",
        )

    def test_parses_the_search_envelope(self) -> None:
        """
        Test that the ``{total_count, incomplete_results, items}``
        envelope is parsed into a :py:class:`SearchPage` of repositories.
        """
        backend = StubBackend(Response(200, body=_envelope("cpython", "peps", total=1234)))
        client = GitHubClient(backend)

        page = client.send(SearchRepos(q="python"))

        self.assertIsInstance(page, SearchPage)
        self.assertEqual(page.total_count, 1234)
        self.assertFalse(page.incomplete_results)
        self.assertEqual([repo.full_name for repo in page], ["python/cpython", "python/peps"])
        self.assertIsNone(page.next)

    def test_link_header_yields_next_operation(self) -> None:
        """
        Test that search pages paginate like the listings: a ``Link:
        rel="next"`` becomes the same search with ``page`` incremented —
        and the envelope fields survive the attachment.
        """
        backend = StubBackend(
            Response(
                200,
                body=_envelope("cpython", total=50),
                headers={"Link": '<https://api.github.com/x?page=2>; rel="next"'},
            )
        )
        client = GitHubClient(backend)

        page = client.send(SearchRepos(q="python", sort=RepoSearchSort.STARS))

        self.assertEqual(page.total_count, 50)
        self.assertEqual(page.next, SearchRepos(q="python", sort=RepoSearchSort.STARS, page=2))

    def test_all_items_walks_search_pages(self) -> None:
        """
        Test that the pagination helpers accept search operations too and
        flatten the envelope pages.
        """
        backend = StubBackend(
            Response(
                200,
                body=_envelope("cpython", "peps", total=3),
                headers={"Link": '<https://api.github.com/x?page=2>; rel="next"'},
            ),
            Response(200, body=_envelope("mypy", total=3)),
        )
        client = GitHubClient(backend)

        names = [repo.name for repo in all_items(client, SearchRepos(q="python", per_page=2))]

        self.assertEqual(names, ["cpython", "peps", "mypy"])
        self.assertEqual(len(backend.requests), 2)
