import unittest
from datetime import datetime
from datetime import timezone

from action0.github import IssueComment

USER_PAYLOAD = {
    "login": "octocat",
    "id": 1,
    "html_url": "https://github.com/octocat",
    "type": "User",
}

COMMENT_PAYLOAD = {
    "id": 301,
    "html_url": "https://github.com/octo/demo/issues/1347#issuecomment-301",
    "body": "Me too!",
    "user": USER_PAYLOAD,
    "created_at": "2026-08-01T10:00:00Z",
    "updated_at": "2026-08-01T11:00:00Z",
}


class IssueCommentTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.comment.IssueComment`
    """

    def test_from_json(self) -> None:
        """
        Test that a comment payload is mapped onto the dataclass.
        """
        comment = IssueComment.from_json(COMMENT_PAYLOAD)

        self.assertEqual(comment.id, 301)
        self.assertEqual(comment.body, "Me too!")
        assert comment.user is not None
        self.assertEqual(comment.user.login, "octocat")
        self.assertEqual(comment.created_at, datetime(2026, 8, 1, 10, tzinfo=timezone.utc))
        self.assertEqual(comment.updated_at, datetime(2026, 8, 1, 11, tzinfo=timezone.utc))

    def test_from_json_minimal(self) -> None:
        """
        Test that a payload with only the required keys maps the
        optional fields to their defaults (``user`` can be null for
        deleted accounts).
        """
        comment = IssueComment.from_json(
            {
                "id": 302,
                "html_url": "https://github.com/octo/demo/issues/1347#issuecomment-302",
                "user": None,
            }
        )

        self.assertEqual(comment.body, "")
        self.assertIsNone(comment.user)
        self.assertIsNone(comment.created_at)
        self.assertIsNone(comment.updated_at)
