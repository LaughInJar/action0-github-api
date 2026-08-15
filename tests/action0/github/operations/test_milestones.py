import json
import unittest
from datetime import datetime
from datetime import timezone

from action0.client.testing import StubBackend
from action0.github import CreateMilestone
from action0.github import DeleteMilestone
from action0.github import GitHubClient
from action0.github import IssueState
from action0.github import IssueStateFilter
from action0.github import ListMilestones
from action0.github import Milestone
from action0.github import MilestoneSort
from action0.github import SortDirection
from action0.github import UpdateMilestone
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


class CreateMilestoneTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.milestones.CreateMilestone`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the POST body — the ``due_on`` datetime as ISO 8601 in the
        JSON — and the parsing.
        """
        backend = StubBackend(Response(201, body=json.dumps(MILESTONE_PAYLOAD)))
        client = GitHubClient(backend, token="ghp_secret")

        milestone = client.send(
            CreateMilestone(
                owner="octo",
                repo="demo",
                title="v1.0",
                due_on=datetime(2026, 10, 9, 23, 39, 1, tzinfo=timezone.utc),
            )
        )

        body = backend.requests[0].body_str()
        assert body is not None
        self.assertEqual(
            json.loads(body),
            {"title": "v1.0", "due_on": "2026-10-09T23:39:01+00:00"},
        )
        self.assertEqual(milestone.number, 1)

    def test_update_and_delete(self) -> None:
        """
        Test closing via PATCH and the 204 delete.
        """
        backend = StubBackend(Response(200, body=json.dumps(MILESTONE_PAYLOAD)), Response(204))
        client = GitHubClient(backend, token="ghp_secret")

        client.send(
            UpdateMilestone(owner="octo", repo="demo", milestone_number=1, state=IssueState.CLOSED)
        )
        result = client.send(DeleteMilestone(owner="octo", repo="demo", milestone_number=1))

        patch, delete = backend.requests
        self.assertEqual(patch.method, "PATCH")
        body = patch.body_str()
        assert body is not None
        self.assertEqual(json.loads(body), {"state": "closed"})
        self.assertEqual(delete.method, "DELETE")
        self.assertEqual(
            delete.url.as_str(), "https://api.github.com/repos/octo/demo/milestones/1"
        )
        self.assertIsNone(result)
