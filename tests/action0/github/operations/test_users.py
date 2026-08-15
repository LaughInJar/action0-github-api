import json
import unittest

from action0.client.testing import StubBackend
from action0.github import GetAuthenticatedUser
from action0.github import GetUser
from action0.github import GitHubClient
from action0.github import ListFollowers
from action0.github import ListUserOrgs
from action0.github import SimpleOrganization
from action0.github import User
from action0.req import Response

USER_PAYLOAD = {
    "login": "gvanrossum",
    "id": 2894642,
    "html_url": "https://github.com/gvanrossum",
    "type": "User",
    "name": "Guido van Rossum",
    "followers": 20000,
}


class GetUserTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.users.GetUser`
    """

    def test_request(self) -> None:
        """
        Test the request shape: GET, rendered path template.
        """
        request = GetUser(username="gvanrossum").as_request("https://api.github.com")

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url.as_str(), "https://api.github.com/users/gvanrossum")

    def test_parses_into_user(self) -> None:
        """
        Test that a 200 payload is parsed into a :py:class:`User`.
        """
        backend = StubBackend(Response(200, body=json.dumps(USER_PAYLOAD)))
        client = GitHubClient(backend)

        user = client.send(GetUser(username="gvanrossum"))

        self.assertIsInstance(user, User)
        self.assertEqual(user.name, "Guido van Rossum")


class GetAuthenticatedUserTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.users.GetAuthenticatedUser`
    """

    def test_request_and_parse(self) -> None:
        """
        Test that the operation hits ``/user`` (with the token attached
        by the client) and parses into a :py:class:`User`.
        """
        backend = StubBackend(Response(200, body=json.dumps(USER_PAYLOAD)))
        client = GitHubClient(backend, token="ghp_secret")

        user = client.send(GetAuthenticatedUser())

        self.assertEqual(user.login, "gvanrossum")
        request = backend.requests[0]
        self.assertEqual(request.url.as_str(), "https://api.github.com/user")
        self.assertEqual(request.headers["Authorization"], "Bearer ghp_secret")


class ListFollowersTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.users.ListFollowers`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the request path and the follower parsing.
        """
        payload = [{"login": "octocat", "id": 1, "html_url": "…", "type": "User"}]
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend)

        page = client.send(ListFollowers(username="gvanrossum"))

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/users/gvanrossum/followers?per_page=30&page=1",
        )
        self.assertEqual([user.login for user in page], ["octocat"])


class ListUserOrgsTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.users.ListUserOrgs`
    """

    def test_request_and_parse(self) -> None:
        """
        Test that the membership entries parse into
        :py:class:`SimpleOrganization` — the payloads carry no profile
        fields, not even an ``html_url``.
        """
        payload = [{"login": "python", "id": 1525981, "description": "The language"}]
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend)

        page = client.send(ListUserOrgs(username="gvanrossum"))

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/users/gvanrossum/orgs?per_page=30&page=1",
        )
        self.assertIsInstance(page[0], SimpleOrganization)
        self.assertEqual(page[0].login, "python")
