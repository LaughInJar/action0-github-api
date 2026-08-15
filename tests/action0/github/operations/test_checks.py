import json
import unittest

from action0.client.testing import StubBackend
from action0.github import CheckRunStatusFilter
from action0.github import GitHubClient
from action0.github import ListCheckRunsForRef
from action0.req import Response

RUNS_ENVELOPE = {
    "total_count": 1,
    "check_runs": [
        {
            "id": 4,
            "name": "build",
            "status": "completed",
            "conclusion": "success",
            "head_sha": "6dcb09b5",
        }
    ],
}


class ListCheckRunsForRefTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.checks.ListCheckRunsForRef`
    """

    def test_request_filters(self) -> None:
        """
        Test the filtered request.
        """
        request = ListCheckRunsForRef(
            owner="octo",
            repo="demo",
            ref="main",
            check_name="build",
            status=CheckRunStatusFilter.COMPLETED,
        ).as_request("https://api.github.com")

        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/commits/main/check-runs"
            "?per_page=30&page=1&check_name=build&status=completed",
        )

    def test_unwraps_envelope_and_paginates(self) -> None:
        """
        Test the one enveloped listing: the ``check_runs`` array is
        unwrapped into the usual page, and the ``Link`` header still
        drives pagination.
        """
        backend = StubBackend(
            Response(
                200,
                headers={"Link": '<https://api.github.com/...&page=2>; rel="next"'},
                body=json.dumps(RUNS_ENVELOPE),
            )
        )
        client = GitHubClient(backend)

        page = client.send(ListCheckRunsForRef(owner="octo", repo="demo", ref="main"))

        self.assertEqual([run.name for run in page], ["build"])
        assert page.next is not None
        self.assertEqual(
            page.next, ListCheckRunsForRef(owner="octo", repo="demo", ref="main", page=2)
        )
