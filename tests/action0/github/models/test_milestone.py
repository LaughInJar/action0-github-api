import unittest

from action0.github import IssueState
from action0.github import Milestone

MILESTONE_PAYLOAD = {
    "id": 1002604,
    "number": 1,
    "title": "v1.0",
    "state": "open",
    "html_url": "https://github.com/octo/demo/milestones/v1.0",
    "description": "Tracking milestone for version 1.0",
    "open_issues": 4,
    "closed_issues": 8,
    "due_on": "2026-10-09T23:39:01Z",
    "created_at": "2026-04-10T20:09:31Z",
}


class MilestoneTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.milestone.Milestone`
    """

    def test_from_json(self) -> None:
        """
        Test that the payload is parsed — the state reuses the issue
        vocabulary.
        """
        milestone = Milestone.from_json(MILESTONE_PAYLOAD)

        self.assertEqual(milestone.number, 1)
        self.assertEqual(milestone.title, "v1.0")
        self.assertEqual(milestone.state, IssueState.OPEN)
        self.assertEqual(milestone.open_issues, 4)
        assert milestone.due_on is not None
        self.assertEqual(milestone.due_on.month, 10)
