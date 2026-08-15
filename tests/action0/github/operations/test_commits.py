import json
import unittest
from datetime import datetime
from datetime import timezone

from action0.client.testing import StubBackend
from action0.github import CompareCommits
from action0.github import Comparison
from action0.github import ComparisonStatus
from action0.github import GetCommit
from action0.github import GitHubClient
from action0.github import ListCommits
from action0.github import ListPullsForCommit
from action0.github import PullRequest
from action0.req import Response

COMMIT_PAYLOAD = {
    "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
    "html_url": "https://github.com/octo/demo/commit/6dcb09b5b57875f334f61aebed695e2e4193db5e",
    "commit": {"message": "Fix all the bugs"},
    "parents": [{"sha": "553c2077f0edc3d5dc5d17262f6aa498e69d6f8e"}],
}


class ListCommitsTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.commits.ListCommits`
    """

    def test_request_defaults(self) -> None:
        """
        Test the default request: the ``None`` filters are omitted, the
        pagination defaults are sent.
        """
        request = ListCommits(owner="octo", repo="demo").as_request("https://api.github.com")

        self.assertEqual(request.method, "GET")
        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/commits?per_page=30&page=1",
        )

    def test_request_filters(self) -> None:
        """
        Test the fully filtered request: ``file_path`` goes on the wire
        as ``path`` (its aliased GitHub name), the datetimes as ISO 8601.
        """
        request = ListCommits(
            owner="octo",
            repo="demo",
            sha="main",
            file_path="src/app.py",
            author="octocat",
            committer="web-flow",
            since=datetime(2026, 8, 1, tzinfo=timezone.utc),
            until=datetime(2026, 8, 15, tzinfo=timezone.utc),
        ).as_request("https://api.github.com")

        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/commits"
            "?per_page=30&page=1&sha=main&path=src%2Fapp.py&author=octocat&committer=web-flow"
            "&since=2026-08-01T00%3A00%3A00%2B00%3A00&until=2026-08-15T00%3A00%3A00%2B00%3A00",
        )

    def test_parses_into_commit_page(self) -> None:
        """
        Test that a JSON array payload is parsed into a
        :py:class:`~action0.github.models.page.Page` of
        :py:class:`~action0.github.models.commit.Commit`, with the next
        page attached from the ``Link`` header.
        """
        backend = StubBackend(
            Response(
                200,
                headers={
                    "Link": '<https://api.github.com/repositories/1/commits?page=2>; rel="next"'
                },
                body=json.dumps([COMMIT_PAYLOAD]),
            )
        )
        client = GitHubClient(backend)

        page = client.send(ListCommits(owner="octo", repo="demo"))

        self.assertEqual([commit.message for commit in page], ["Fix all the bugs"])
        assert page.next is not None
        self.assertEqual(page.next, ListCommits(owner="octo", repo="demo", page=2))


class GetCommitTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.commits.GetCommit`
    """

    def test_request_accepts_any_ref(self) -> None:
        """
        Test the request shape: ``ref`` may be a branch name, not just a
        sha.
        """
        request = GetCommit(owner="octo", repo="demo", ref="main").as_request(
            "https://api.github.com"
        )

        self.assertEqual(request.method, "GET")
        self.assertEqual(
            request.url.as_str(), "https://api.github.com/repos/octo/demo/commits/main"
        )

    def test_parses_into_commit(self) -> None:
        """
        Test that the payload is parsed into a
        :py:class:`~action0.github.models.commit.Commit`, including the
        diff statistics only this endpoint carries.
        """
        payload = dict(
            COMMIT_PAYLOAD,
            stats={"additions": 10, "deletions": 3, "total": 13},
            files=[
                {
                    "filename": "src/app.py",
                    "status": "modified",
                    "additions": 10,
                    "deletions": 3,
                    "changes": 13,
                }
            ],
        )
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend)

        commit = client.send(GetCommit(owner="octo", repo="demo", ref="6dcb09b5"))

        self.assertEqual(commit.additions, 10)
        assert commit.files is not None
        self.assertEqual(commit.files[0].filename, "src/app.py")


class CompareCommitsTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.commits.CompareCommits`
    """

    def test_request_joins_base_and_head(self) -> None:
        """
        Test the request shape: the two ref fields land in one
        ``{base}...{head}`` path segment.
        """
        request = CompareCommits(owner="octo", repo="demo", base="main", head="topic").as_request(
            "https://api.github.com"
        )

        self.assertEqual(request.method, "GET")
        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/compare/main...topic",
        )

    def test_parses_into_comparison(self) -> None:
        """
        Test that the payload is parsed into a
        :py:class:`~action0.github.models.comparison.Comparison`.
        """
        payload = {
            "status": "ahead",
            "ahead_by": 1,
            "behind_by": 0,
            "total_commits": 1,
            "html_url": "https://github.com/octo/demo/compare/main...topic",
            "merge_base_commit": COMMIT_PAYLOAD,
            "commits": [COMMIT_PAYLOAD],
            "files": [],
        }
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend)

        comparison = client.send(
            CompareCommits(owner="octo", repo="demo", base="main", head="topic")
        )

        self.assertIsInstance(comparison, Comparison)
        self.assertEqual(comparison.status, ComparisonStatus.AHEAD)
        self.assertEqual(comparison.commits[0].sha, COMMIT_PAYLOAD["sha"])


class ListPullsForCommitTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.commits.ListPullsForCommit`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the reverse lookup: sha in, pull requests out.
        """
        payload = [
            {
                "id": 201,
                "number": 12,
                "title": "Amazing new feature",
                "state": "closed",
                "html_url": "https://github.com/octo/demo/pull/12",
                "head": {"label": "octo:topic", "ref": "topic", "sha": "aa218f56"},
                "base": {"label": "octo:main", "ref": "main", "sha": "6dcb09b5"},
            }
        ]
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend)

        page = client.send(
            ListPullsForCommit(
                owner="octo",
                repo="demo",
                commit_sha="6dcb09b5b57875f334f61aebed695e2e4193db5e",
            )
        )

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/commits/"
            "6dcb09b5b57875f334f61aebed695e2e4193db5e/pulls?per_page=30&page=1",
        )
        self.assertEqual([pull.number for pull in page], [12])
        self.assertIsInstance(page[0], PullRequest)
