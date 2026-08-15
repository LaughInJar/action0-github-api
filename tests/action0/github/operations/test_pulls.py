import json
import unittest

from action0.client.testing import StubBackend
from action0.github import CreatePull
from action0.github import GetPull
from action0.github import GitHubClient
from action0.github import ListPulls
from action0.github import PullRequest
from action0.github import PullSort
from action0.github import PullStateFilter
from action0.github import SortDirection
from action0.req import Response

PULL_PAYLOAD = {
    "id": 201,
    "number": 1347,
    "title": "Amazing new feature",
    "state": "open",
    "html_url": "https://github.com/octo/demo/pull/1347",
    "head": {"label": "octocat:new-topic", "ref": "new-topic", "sha": "aa218f56"},
    "base": {"label": "octo:main", "ref": "main", "sha": "6dcb09b5"},
    "user": None,
}


class ListPullsTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.pulls.ListPulls`
    """

    def test_request_defaults(self) -> None:
        """
        Test the default request: the ``None`` filters are omitted, the
        pagination defaults are sent.
        """
        request = ListPulls(owner="octo", repo="demo").as_request("https://api.github.com")

        self.assertEqual(request.method, "GET")
        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/pulls?per_page=30&page=1",
        )

    def test_request_filters(self) -> None:
        """
        Test the fully filtered request: enums as their wire values —
        including ``long-running``, whose value is not its member name.
        """
        request = ListPulls(
            owner="octo",
            repo="demo",
            state=PullStateFilter.ALL,
            head="octocat:new-topic",
            base="main",
            sort=PullSort.LONG_RUNNING,
            direction=SortDirection.ASC,
        ).as_request("https://api.github.com")

        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/pulls"
            "?per_page=30&page=1&state=all&head=octocat%3Anew-topic"
            "&base=main&sort=long-running&direction=asc",
        )

    def test_parses_into_pull_page(self) -> None:
        """
        Test that a JSON array payload is parsed into a
        :py:class:`~action0.github.models.page.Page` of
        :py:class:`PullRequest`.
        """
        backend = StubBackend(Response(200, body=json.dumps([PULL_PAYLOAD])))
        client = GitHubClient(backend)

        page = client.send(ListPulls(owner="octo", repo="demo"))

        self.assertEqual([pull.number for pull in page], [1347])
        self.assertIsInstance(page[0], PullRequest)
        self.assertIsNone(page.next)


class GetPullTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.pulls.GetPull`
    """

    def test_request(self) -> None:
        """
        Test the request shape: the integer ``pull_number`` lands in the
        path.
        """
        request = GetPull(owner="octo", repo="demo", pull_number=1347).as_request(
            "https://api.github.com"
        )

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url.as_str(), "https://api.github.com/repos/octo/demo/pulls/1347")

    def test_parses_into_pull(self) -> None:
        """
        Test that the payload is parsed into a :py:class:`PullRequest`,
        including the statistics only this endpoint carries.
        """
        payload = dict(PULL_PAYLOAD, mergeable=True, commits=3, changed_files=5)
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend)

        pull = client.send(GetPull(owner="octo", repo="demo", pull_number=1347))

        self.assertIsInstance(pull, PullRequest)
        self.assertEqual(pull.number, 1347)
        self.assertTrue(pull.mergeable)
        self.assertEqual(pull.changed_files, 5)


class CreatePullTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.pulls.CreatePull`
    """

    def test_request(self) -> None:
        """
        Test the request shape: POST, JSON body with the ``None`` fields
        omitted, JSON content type.
        """
        request = CreatePull(
            owner="octo",
            repo="demo",
            title="Amazing new feature",
            head="octocat:new-topic",
            base="main",
            draft=True,
        ).as_request("https://api.github.com")

        self.assertEqual(request.method, "POST")
        self.assertEqual(request.url.as_str(), "https://api.github.com/repos/octo/demo/pulls")
        self.assertEqual(request.headers["Content-Type"], "application/json")
        body = request.body_str()
        assert body is not None  # narrows the Optional for the type checkers
        self.assertEqual(
            json.loads(body),
            # no "body" key: None fields are omitted from the body
            {
                "title": "Amazing new feature",
                "head": "octocat:new-topic",
                "base": "main",
                "draft": True,
            },
        )

    def test_parses_created_pull(self) -> None:
        """
        Test that the 201 payload is parsed into the created
        :py:class:`PullRequest`.
        """
        backend = StubBackend(Response(201, body=json.dumps(PULL_PAYLOAD)))
        client = GitHubClient(backend, token="ghp_secret")

        pull = client.send(
            CreatePull(
                owner="octo",
                repo="demo",
                title="Amazing new feature",
                head="octocat:new-topic",
                base="main",
            )
        )

        self.assertIsInstance(pull, PullRequest)
        self.assertEqual(pull.number, 1347)
