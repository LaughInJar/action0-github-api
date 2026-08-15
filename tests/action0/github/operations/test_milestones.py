import json
import unittest

from action0.client.testing import StubBackend
from action0.github import GitHubClient
from action0.github import IssueStateFilter
from action0.github import ListMilestones
from action0.github import Milestone
from action0.github import MilestoneSort
from action0.github import SortDirection
from action0.req import Response

MILESTONE_PAYLOAD = {
    "id": 1002604,
    "number": 1,
    "title": "v1.0",
    "state": "open",
    "html_url": "https://github.com/octo/demo/milestones/v1.0",
}


class ListMilestonesTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.milestones.ListMilestones`
    """

    def test_request_filters(self) -> None:
        """
        Test the fully filtered request — the state filter reuses the
        issue vocabulary.
        """
        request = ListMilestones(
            owner="octo",
            repo="demo",
            state=IssueStateFilter.ALL,
            sort=MilestoneSort.COMPLETENESS,
            direction=SortDirection.DESC,
        ).as_request("https://api.github.com")

        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/milestones"
            "?per_page=30&page=1&state=all&sort=completeness&direction=desc",
        )

    def test_parses_into_milestone_page(self) -> None:
        """
        Test that the JSON array is parsed into a page of
        :py:class:`Milestone`.
        """
        backend = StubBackend(Response(200, body=json.dumps([MILESTONE_PAYLOAD])))
        client = GitHubClient(backend)

        page = client.send(ListMilestones(owner="octo", repo="demo"))

        self.assertEqual([milestone.title for milestone in page], ["v1.0"])
        self.assertIsInstance(page[0], Milestone)
