import unittest

from action0.client.testing import StubBackend
from action0.github import GetRepo
from action0.github import GitHubClient
from action0.github import __version__
from action0.req import Request
from action0.req import Response

MINIMAL_REPO_BODY = (
    '{"id": 1, "name": "cpython", "full_name": "python/cpython",'
    ' "owner": {"login": "python", "id": 2,'
    ' "html_url": "https://github.com/python", "type": "Organization"},'
    ' "private": false, "html_url": "https://github.com/python/cpython",'
    ' "default_branch": "main"}'
)


class GitHubClientTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.client.GitHubClient`
    """

    def test_default_headers(self) -> None:
        """
        Test that every request carries GitHub's recommended headers.
        """
        backend = StubBackend(Response(200, body=MINIMAL_REPO_BODY))
        client = GitHubClient(backend)
        client.send(GetRepo(owner="python", repo="cpython"))

        headers = backend.requests[0].headers
        self.assertEqual(headers["Accept"], "application/vnd.github+json")
        self.assertEqual(headers["X-GitHub-Api-Version"], "2022-11-28")
        self.assertEqual(headers["User-Agent"], f"action0-github-api/{__version__}")

    def test_token_becomes_bearer_auth(self) -> None:
        """
        Test that a given token is sent as an ``Authorization: Bearer``.
        """
        backend = StubBackend(Response(200, body=MINIMAL_REPO_BODY))
        client = GitHubClient(backend, token="ghp_secret")
        client.send(GetRepo(owner="python", repo="cpython"))

        self.assertEqual(backend.requests[0].headers["Authorization"], "Bearer ghp_secret")

    def test_no_token_no_authorization_header(self) -> None:
        """
        Test that without a token no ``Authorization`` header is sent.
        """
        backend = StubBackend(Response(200, body=MINIMAL_REPO_BODY))
        client = GitHubClient(backend)
        client.send(GetRepo(owner="python", repo="cpython"))

        self.assertNotIn("Authorization", backend.requests[0].headers)

    def test_request_set_headers_win_over_defaults(self) -> None:
        """
        Test that the defaults only fill gaps: a header the request sets
        itself is left alone.
        """
        client = GitHubClient(StubBackend(), token="ghp_secret")
        request = Request("https://api.github.com/rate_limit")
        request.headers.add("User-Agent", "my-app/1.0")

        prepared = client.prepare(request)

        self.assertEqual(prepared.headers["User-Agent"], "my-app/1.0")
        # the other defaults still filled their gaps
        self.assertEqual(prepared.headers["Authorization"], "Bearer ghp_secret")

    def test_base_url_override_for_enterprise(self) -> None:
        """
        Test that a custom base URL (GitHub Enterprise Server) is used.
        """
        backend = StubBackend(Response(200, body=MINIMAL_REPO_BODY))
        client = GitHubClient(backend, base_url="https://ghe.example.com/api/v3")
        client.send(GetRepo(owner="python", repo="cpython"))

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://ghe.example.com/api/v3/repos/python/cpython",
        )
