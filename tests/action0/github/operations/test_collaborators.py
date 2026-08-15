import json
import unittest

from action0.client.testing import StubBackend
from action0.github import CollaboratorAffiliation
from action0.github import GetCollaboratorPermission
from action0.github import GitHubClient
from action0.github import ListCollaborators
from action0.req import Response


class ListCollaboratorsTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.collaborators.ListCollaborators`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the filtered request and the member parsing.
        """
        payload = [{"login": "octocat", "id": 1, "html_url": "…", "type": "User"}]
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend, token="ghp_secret")

        page = client.send(
            ListCollaborators(
                owner="octo", repo="demo", affiliation=CollaboratorAffiliation.OUTSIDE
            )
        )

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/collaborators"
            "?per_page=30&page=1&affiliation=outside",
        )
        self.assertEqual([user.login for user in page], ["octocat"])


class GetCollaboratorPermissionTestCase(unittest.TestCase):
    """
    tests for
    :py:class:`action0.github.operations.collaborators.GetCollaboratorPermission`
    """

    def test_request_and_parse(self) -> None:
        """
        Test that the answer is reduced to the permission string.
        """
        payload = {
            "permission": "write",
            "role_name": "write",
            "user": {"login": "octocat", "id": 1, "html_url": "…", "type": "User"},
        }
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend, token="ghp_secret")

        permission = client.send(
            GetCollaboratorPermission(owner="octo", repo="demo", username="octocat")
        )

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/collaborators/octocat/permission",
        )
        self.assertEqual(permission, "write")
