import json
import unittest

from action0.client.testing import StubBackend
from action0.github import Branch
from action0.github import GetBranch
from action0.github import GitHubClient
from action0.github import ListBranches
from action0.req import Response


class ListBranchesTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.branches.ListBranches`
    """

    def test_request_bool_filter(self) -> None:
        """
        Test the first boolean query parameter — serialized web-style.
        """
        request = ListBranches(owner="octo", repo="demo", protected=False).as_request(
            "https://api.github.com"
        )

        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/branches?per_page=30&page=1&protected=false",
        )

    def test_parses_into_branch_page(self) -> None:
        """
        Test that the array is parsed into a page of :py:class:`Branch`.
        """
        payload = [
            {"name": "main", "commit": {"sha": "6dcb09b5"}, "protected": True},
            {"name": "topic", "commit": {"sha": "aa218f56"}},
        ]
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend)

        page = client.send(ListBranches(owner="octo", repo="demo"))

        self.assertEqual([branch.name for branch in page], ["main", "topic"])
        self.assertIsInstance(page[0], Branch)
        self.assertTrue(page[0].protected)
        self.assertFalse(page[1].protected)


class GetBranchTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.branches.GetBranch`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the request path and that the full tip commit only this
        endpoint carries is parsed.
        """
        payload = {
            "name": "main",
            "commit": {
                "sha": "6dcb09b5",
                "html_url": "https://github.com/octo/demo/commit/6dcb09b5",
                "commit": {"message": "Fix all the bugs"},
                "parents": [],
            },
            "protected": False,
        }
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend)

        branch = client.send(GetBranch(owner="octo", repo="demo", branch="main"))

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/branches/main",
        )
        assert branch.commit is not None
        self.assertEqual(branch.commit.message, "Fix all the bugs")
