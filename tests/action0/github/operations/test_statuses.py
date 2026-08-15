import json
import unittest

from action0.client.testing import StubBackend
from action0.github import GetCombinedStatus
from action0.github import GitHubClient
from action0.github import StatusState
from action0.req import Response


class GetCombinedStatusTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.statuses.GetCombinedStatus`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the request path and the combined status parsing.
        """
        payload = {
            "state": "success",
            "sha": "6dcb09b5",
            "total_count": 1,
            "statuses": [{"state": "success", "context": "ci/build"}],
        }
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend)

        combined = client.send(GetCombinedStatus(owner="octo", repo="demo", ref="main"))

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/commits/main/status",
        )
        self.assertEqual(combined.state, StatusState.SUCCESS)
        self.assertEqual(combined.statuses[0].context, "ci/build")
