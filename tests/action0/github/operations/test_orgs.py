import json
import unittest

from action0.client.testing import StubBackend
from action0.github import GetOrg
from action0.github import GitHubClient
from action0.github import ListOrgMembers
from action0.github import OrgMemberRole
from action0.github import SimpleUser
from action0.req import Response

ORG_PAYLOAD = {
    "login": "python",
    "id": 1525981,
    "html_url": "https://github.com/python",
    "name": "Python",
}

MEMBER_PAYLOAD = {
    "login": "octocat",
    "id": 1,
    "html_url": "https://github.com/octocat",
    "type": "User",
}


class GetOrgTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.orgs.GetOrg`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the request path and that the payload is parsed into the
        :py:class:`Organization`.
        """
        backend = StubBackend(Response(200, body=json.dumps(ORG_PAYLOAD)))
        client = GitHubClient(backend)

        organization = client.send(GetOrg(org="python"))

        self.assertEqual(backend.requests[0].url.as_str(), "https://api.github.com/orgs/python")
        self.assertEqual(organization.login, "python")
        self.assertEqual(organization.name, "Python")


class ListOrgMembersTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.orgs.ListOrgMembers`
    """

    def test_request_with_role(self) -> None:
        """
        Test the filtered request: the role enum as its wire value.
        """
        request = ListOrgMembers(org="python", role=OrgMemberRole.MEMBER).as_request(
            "https://api.github.com"
        )

        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/orgs/python/members?per_page=30&page=1&role=member",
        )

    def test_parses_into_member_page(self) -> None:
        """
        Test that the JSON array is parsed into a page of
        :py:class:`SimpleUser` (members carry no profile fields).
        """
        backend = StubBackend(Response(200, body=json.dumps([MEMBER_PAYLOAD])))
        client = GitHubClient(backend)

        page = client.send(ListOrgMembers(org="python"))

        self.assertEqual([member.login for member in page], ["octocat"])
        self.assertIsInstance(page[0], SimpleUser)
