import json
import unittest

from action0.client import APIError
from action0.client.testing import StubBackend
from action0.github import GetRepo
from action0.github import GitHubClient
from action0.github import ListOrgRepos
from action0.github import ListUserRepos
from action0.github import Repo
from action0.github import RepoSort
from action0.github import SortDirection
from action0.github import UserRepoType
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


class ListReposTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.repos.ListOrgRepos`
    and :py:class:`action0.github.operations.repos.ListUserRepos`
    """

    def test_request_defaults(self) -> None:
        """
        Test the default request: the ``None`` filters are omitted, the
        pagination defaults are sent.
        """
        request = ListOrgRepos(org="python").as_request("https://api.github.com")

        self.assertEqual(request.method, "GET")
        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/orgs/python/repos?per_page=30&page=1",
        )

    def test_request_enums_serialize_to_values(self) -> None:
        """
        Test that the enum query fields end up as their wire values.
        """
        request = ListUserRepos(
            username="gvanrossum",
            type=UserRepoType.OWNER,
            sort=RepoSort.PUSHED,
            direction=SortDirection.DESC,
            per_page=100,
            page=2,
        ).as_request("https://api.github.com")

        self.assertEqual(
            request.url.as_str(),
            # per_page/page first: they live on the PaginatedOperation base
            "https://api.github.com/users/gvanrossum/repos"
            "?per_page=100&page=2&sort=pushed&direction=desc&type=owner",
        )

    def test_parses_into_repo_list(self) -> None:
        """
        Test that a JSON array payload is parsed into a list of
        :py:class:`Repo`.
        """
        second = dict(REPO_PAYLOAD, id=4534, name="peps", full_name="python/peps")
        backend = StubBackend(Response(200, body=json.dumps([REPO_PAYLOAD, second])))
        client = GitHubClient(backend)

        repos = client.send(ListOrgRepos(org="python", sort=RepoSort.FULL_NAME))

        self.assertEqual([repo.full_name for repo in repos], ["python/cpython", "python/peps"])
        for repo in repos:
            self.assertIsInstance(repo, Repo)

    def test_parses_empty_page(self) -> None:
        """
        Test that an empty page (past the last one) parses to an empty list.
        """
        backend = StubBackend(Response(200, body="[]"))
        client = GitHubClient(backend)

        self.assertEqual(client.send(ListOrgRepos(org="python", page=99)), [])
