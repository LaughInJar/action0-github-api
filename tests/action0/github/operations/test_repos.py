import json
import unittest

from action0.client import APIError
from action0.client.testing import StubBackend
from action0.github import GetRepo
from action0.github import GitHubClient
from action0.github import Repo
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


class GetRepoTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.repos.GetRepo`
    """

    def test_request(self) -> None:
        """
        Test the request shape: GET, rendered path template, GitHub's
        media type.
        """
        request = GetRepo(owner="python", repo="cpython").as_request("https://api.github.com")

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url.as_str(), "https://api.github.com/repos/python/cpython")
        self.assertEqual(request.headers["Accept"], "application/vnd.github+json")

    def test_parses_into_repo(self) -> None:
        """
        Test that a 200 payload is parsed into a :py:class:`Repo`.
        """
        backend = StubBackend(Response(200, body=json.dumps(REPO_PAYLOAD)))
        client = GitHubClient(backend)

        repo = client.send(GetRepo(owner="python", repo="cpython"))

        self.assertIsInstance(repo, Repo)
        self.assertEqual(repo.full_name, "python/cpython")
        self.assertEqual(repo.owner.login, "python")

    def test_not_found_raises_api_error(self) -> None:
        """
        Test that a 404 raises :py:class:`~action0.client.errors.APIError`
        with the response attached.
        """
        body = '{"message": "Not Found"}'
        backend = StubBackend(Response(404, body=body))
        client = GitHubClient(backend)

        with self.assertRaises(APIError) as caught:
            client.send(GetRepo(owner="python", repo="no-such-repo"))

        response = caught.exception.response
        assert response is not None  # narrows the Optional for the type checkers
        self.assertEqual(response.status, 404)
