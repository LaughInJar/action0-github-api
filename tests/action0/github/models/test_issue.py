import unittest
from datetime import datetime
from datetime import timezone

from action0.github import Issue
from action0.github import IssueState
from action0.github import Label

USER_PAYLOAD = {
    "login": "octocat",
    "id": 1,
    "html_url": "https://github.com/octocat",
    "type": "User",
}

ISSUE_PAYLOAD = {
    "id": 101,
    "number": 1347,
    "title": "Found a bug",
    "state": "open",
    "html_url": "https://github.com/octo/demo/issues/1347",
    "user": USER_PAYLOAD,
    "body": "It does not work.",
    "labels": [{"id": 1, "name": "bug", "color": "f29513"}, "help wanted"],
    "assignees": [USER_PAYLOAD],
    "comments": 3,
    "locked": False,
    "created_at": "2026-08-01T10:00:00Z",
    "updated_at": "2026-08-02T10:00:00Z",
    "closed_at": None,
}


class IssueTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.issue.Issue`
    """

    def test_from_json(self) -> None:
        """
        Test that an issue payload is mapped onto the dataclass — with
        labels arriving as objects and bare strings mixed.
        """
        issue = Issue.from_json(ISSUE_PAYLOAD)

        self.assertEqual(issue.number, 1347)
        self.assertEqual(issue.state, IssueState.OPEN)
        assert issue.user is not None
        self.assertEqual(issue.user.login, "octocat")
        self.assertEqual(
            issue.labels,
            [Label(name="bug", id=1, color="f29513"), Label(name="help wanted")],
        )
        self.assertEqual([assignee.login for assignee in issue.assignees], ["octocat"])
        self.assertEqual(issue.created_at, datetime(2026, 8, 1, 10, tzinfo=timezone.utc))
        self.assertIsNone(issue.closed_at)
        self.assertFalse(issue.is_pull_request)

    def test_from_json_milestone(self) -> None:
        """
        Test that an assigned milestone is parsed (and its absence stays
        ``None`` — see :py:meth:`test_from_json_minimal`).
        """
        payload = dict(
            ISSUE_PAYLOAD,
            milestone={
                "id": 1002604,
                "number": 1,
                "title": "v1.0",
                "state": "open",
                "html_url": "https://github.com/octo/demo/milestones/v1.0",
            },
        )

        issue = Issue.from_json(payload)

        assert issue.milestone is not None
        self.assertEqual(issue.milestone.title, "v1.0")
        self.assertIsNone(Issue.from_json(ISSUE_PAYLOAD).milestone)

    def test_from_json_pull_request_marker(self) -> None:
        """
        Test that the ``pull_request`` key marks the issue as actually
        being a pull request.
        """
        payload = dict(ISSUE_PAYLOAD, pull_request={"url": "https://api.github.com/..."})

        self.assertTrue(Issue.from_json(payload).is_pull_request)

    def test_from_json_minimal(self) -> None:
        """
        Test that a payload with only the required keys maps the optional
        fields to their defaults (``user`` can be null for deleted
        accounts).
        """
        issue = Issue.from_json(
            {
                "id": 1,
                "number": 2,
                "title": "Ghost issue",
                "state": "closed",
                "html_url": "https://github.com/octo/demo/issues/2",
                "user": None,
            }
        )

        self.assertEqual(issue.state, IssueState.CLOSED)
        self.assertIsNone(issue.user)
        self.assertIsNone(issue.body)
        self.assertEqual(issue.labels, [])
        self.assertEqual(issue.assignees, [])
        self.assertEqual(issue.comments, 0)
        self.assertFalse(issue.locked)
        self.assertIsNone(issue.created_at)
