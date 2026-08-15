import json
import unittest

from action0.client import APIError
from action0.client.testing import StubBackend
from action0.github import Contributor
from action0.github import GetRepo
from action0.github import GetRepoTopics
from action0.github import GitHubClient
from action0.github import ListContributors
from action0.github import ListLanguages
from action0.github import ListOrgRepos
from action0.github import ListRepoTags
from action0.github import ListUserRepos
from action0.github import Page
from action0.github import ReplaceRepoTopics
from action0.github import Repo
from action0.github import RepoSort
from action0.github import SortDirection
from action0.github import Tag
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

    def test_parses_into_repo_page(self) -> None:
        """
        Test that a JSON array payload is parsed into a
        :py:class:`~action0.github.models.page.Page` of :py:class:`Repo` —
        without a ``Link: rel="next"``, it is the last page.
        """
        second = dict(REPO_PAYLOAD, id=4534, name="peps", full_name="python/peps")
        backend = StubBackend(Response(200, body=json.dumps([REPO_PAYLOAD, second])))
        client = GitHubClient(backend)

        page = client.send(ListOrgRepos(org="python", sort=RepoSort.FULL_NAME))

        self.assertIsInstance(page, Page)
        self.assertEqual([repo.full_name for repo in page], ["python/cpython", "python/peps"])
        for repo in page:
            self.assertIsInstance(repo, Repo)
        self.assertIsNone(page.next)

    def test_link_header_yields_next_operation(self) -> None:
        """
        Test that a ``Link: rel="next"`` response header turns into the
        ready-to-send next-page operation — this operation with ``page``
        incremented, all other fields kept.
        """
        backend = StubBackend(
            Response(
                200,
                body=json.dumps([REPO_PAYLOAD]),
                headers={"Link": '<https://api.github.com/x?page=3>; rel="next"'},
            )
        )
        client = GitHubClient(backend)

        page = client.send(ListOrgRepos(org="python", sort=RepoSort.FULL_NAME, page=2))

        self.assertEqual(page.next, ListOrgRepos(org="python", sort=RepoSort.FULL_NAME, page=3))

    def test_parses_empty_page(self) -> None:
        """
        Test that an empty page (past the last one) parses to an empty
        page.
        """
        backend = StubBackend(Response(200, body="[]"))
        client = GitHubClient(backend)

        page = client.send(ListOrgRepos(org="python", page=99))

        self.assertEqual(len(page), 0)
        self.assertFalse(page)


class ListRepoTagsTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.repos.ListRepoTags`
    """

    def test_parses_into_tag_page(self) -> None:
        """
        Test that the array is parsed into a page of :py:class:`Tag`.
        """
        payload = [{"name": "v1.0.0", "commit": {"sha": "6dcb09b5"}}]
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend)

        page = client.send(ListRepoTags(owner="octo", repo="demo"))

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/tags?per_page=30&page=1",
        )
        self.assertEqual([(tag.name, tag.sha) for tag in page], [("v1.0.0", "6dcb09b5")])
        self.assertIsInstance(page[0], Tag)


class ListContributorsTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.repos.ListContributors`
    """

    def test_parses_into_contributor_page(self) -> None:
        """
        Test that the items carry the commit count on top of the user
        core.
        """
        payload = [
            {"login": "octocat", "id": 1, "html_url": "…", "type": "User", "contributions": 42}
        ]
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend)

        page = client.send(ListContributors(owner="octo", repo="demo"))

        self.assertIsInstance(page[0], Contributor)
        self.assertEqual(page[0].login, "octocat")
        self.assertEqual(page[0].contributions, 42)


class ListLanguagesTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.repos.ListLanguages`
    """

    def test_request_and_parse(self) -> None:
        """
        Test that the language → bytes mapping passes through.
        """
        backend = StubBackend(Response(200, body=json.dumps({"Python": 512000, "C": 12000})))
        client = GitHubClient(backend)

        languages = client.send(ListLanguages(owner="octo", repo="demo"))

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/languages",
        )
        self.assertEqual(languages, {"Python": 512000, "C": 12000})


class RepoTopicsTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.repos.GetRepoTopics` and
    :py:class:`action0.github.operations.repos.ReplaceRepoTopics`
    """

    def test_get_unwraps_names(self) -> None:
        """
        Test that the ``{names: [...]}`` envelope is unwrapped.
        """
        backend = StubBackend(Response(200, body=json.dumps({"names": ["api", "python"]})))
        client = GitHubClient(backend)

        topics = client.send(GetRepoTopics(owner="octo", repo="demo"))

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/topics",
        )
        self.assertEqual(topics, ["api", "python"])

    def test_replace_sends_names(self) -> None:
        """
        Test the wholesale PUT: the complete new set as the body.
        """
        backend = StubBackend(Response(200, body=json.dumps({"names": ["api"]})))
        client = GitHubClient(backend, token="ghp_secret")

        topics = client.send(ReplaceRepoTopics(owner="octo", repo="demo", names=["api"]))

        request = backend.requests[0]
        self.assertEqual(request.method, "PUT")
        body = request.body_str()
        assert body is not None
        self.assertEqual(json.loads(body), {"names": ["api"]})
        self.assertEqual(topics, ["api"])
