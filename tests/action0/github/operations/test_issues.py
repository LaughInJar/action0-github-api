import json
import unittest
from datetime import datetime
from datetime import timezone

from action0.client.testing import StubBackend
from action0.github import CreateIssue
from action0.github import GitHubClient
from action0.github import Issue
from action0.github import IssueSort
from action0.github import IssueStateFilter
from action0.github import ListIssues
from action0.github import SortDirection
from action0.req import Response

ISSUE_PAYLOAD = {
    "id": 101,
    "number": 1347,
    "title": "Found a bug",
    "state": "open",
    "html_url": "https://github.com/octo/demo/issues/1347",
    "user": None,
}


class ListIssuesTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.issues.ListIssues`
    """

    def test_request_defaults(self) -> None:
        """
        Test the default request: the ``None`` filters are omitted, the
        pagination defaults are sent.
        """
        request = ListIssues(owner="octo", repo="demo").as_request("https://api.github.com")

        self.assertEqual(request.method, "GET")
        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/issues?per_page=30&page=1",
        )

    def test_request_filters(self) -> None:
        """
        Test the fully filtered request: enums as their wire values, the
        ``since`` datetime as (URL-encoded) ISO 8601.
        """
        request = ListIssues(
            owner="octo",
            repo="demo",
            state=IssueStateFilter.ALL,
            labels="bug,ui",
            sort=IssueSort.COMMENTS,
            direction=SortDirection.ASC,
            since=datetime(2026, 8, 1, tzinfo=timezone.utc),
        ).as_request("https://api.github.com")

        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/issues"
            "?per_page=30&page=1&state=all&labels=bug%2Cui"
            "&sort=comments&direction=asc&since=2026-08-01T00%3A00%3A00%2B00%3A00",
        )

    def test_parses_into_issue_page(self) -> None:
        """
        Test that a JSON array payload is parsed into a
        :py:class:`~action0.github.models.page.Page` of
        :py:class:`Issue`.
        """
        backend = StubBackend(Response(200, body=json.dumps([ISSUE_PAYLOAD])))
        client = GitHubClient(backend)

        page = client.send(ListIssues(owner="octo", repo="demo"))

        self.assertEqual([issue.number for issue in page], [1347])
        self.assertIsInstance(page[0], Issue)
        self.assertIsNone(page.next)


class CreateIssueTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.issues.CreateIssue`
    """

    def test_request(self) -> None:
        """
        Test the request shape: POST, JSON body with the ``None`` fields
        omitted, JSON content type.
        """
        request = CreateIssue(
            owner="octo",
            repo="demo",
            title="Found a bug",
            body="It does not work.",
            labels=["bug"],
        ).as_request("https://api.github.com")

        self.assertEqual(request.method, "POST")
        self.assertEqual(request.url.as_str(), "https://api.github.com/repos/octo/demo/issues")
        self.assertEqual(request.headers["Content-Type"], "application/json")
        body = request.body_str()
        assert body is not None  # narrows the Optional for the type checkers
        self.assertEqual(
            json.loads(body),
            # no "assignees" key: None fields are omitted from the body
            {"title": "Found a bug", "body": "It does not work.", "labels": ["bug"]},
        )

    def test_parses_created_issue(self) -> None:
        """
        Test that the 201 payload is parsed into the created
        :py:class:`Issue`.
        """
        backend = StubBackend(Response(201, body=json.dumps(ISSUE_PAYLOAD)))
        client = GitHubClient(backend, token="ghp_secret")

        issue = client.send(CreateIssue(owner="octo", repo="demo", title="Found a bug"))

        self.assertIsInstance(issue, Issue)
        self.assertEqual(issue.number, 1347)
