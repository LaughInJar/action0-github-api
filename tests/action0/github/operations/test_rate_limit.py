import json
import unittest

from action0.client.testing import StubBackend
from action0.github import GetRateLimit
from action0.github import GitHubClient
from action0.github import RateLimitOverview
from action0.req import Response

OVERVIEW_PAYLOAD = {
    "resources": {
        "core": {"limit": 5000, "remaining": 4999, "used": 1, "reset": 1755264000},
        "search": {"limit": 30, "remaining": 18, "used": 12, "reset": 1755264000},
    },
    "rate": {"limit": 5000, "remaining": 4999, "used": 1, "reset": 1755264000},
}


class GetRateLimitTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.rate_limit.GetRateLimit`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the request path and that the payload is parsed into the
        :py:class:`RateLimitOverview`.
        """
        backend = StubBackend(Response(200, body=json.dumps(OVERVIEW_PAYLOAD)))
        client = GitHubClient(backend, token="ghp_secret")

        overview = client.send(GetRateLimit())

        self.assertEqual(backend.requests[0].url.as_str(), "https://api.github.com/rate_limit")
        self.assertIsInstance(overview, RateLimitOverview)
        self.assertEqual(overview.core.remaining, 4999)
        self.assertEqual(overview.search.limit, 30)
