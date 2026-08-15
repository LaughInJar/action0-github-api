import unittest

from action0.github import Review
from action0.github import ReviewComment
from action0.github import ReviewState


class ReviewTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.review.Review`
    """

    def test_from_json(self) -> None:
        """
        Test that the payload is parsed — the state values are uppercase
        on the wire, unlike GitHub's other state vocabularies.
        """
        review = Review.from_json(
            {
                "id": 80,
                "state": "APPROVED",
                "html_url": "https://github.com/octo/demo/pull/12#pullrequestreview-80",
                "user": {
                    "login": "octocat",
                    "id": 1,
                    "html_url": "https://github.com/octocat",
                    "type": "User",
                },
                "body": "Looks great.",
                "commit_id": "ecdd80bb57125d7ba9641ffaa4d7d2c19d3f3091",
                "submitted_at": "2026-08-14T17:17:52Z",
            }
        )

        self.assertEqual(review.state, ReviewState.APPROVED)
        assert review.user is not None
        self.assertEqual(review.user.login, "octocat")
        self.assertEqual(review.body, "Looks great.")
        self.assertIsNotNone(review.submitted_at)

    def test_from_json_pending(self) -> None:
        """
        Test a pending review: no ``submitted_at`` yet, and a null
        ``body`` becomes the empty string.
        """
        review = Review.from_json(
            {
                "id": 81,
                "state": "PENDING",
                "html_url": "https://github.com/octo/demo/pull/12#pullrequestreview-81",
                "user": None,
                "body": None,
                "submitted_at": None,
            }
        )

        self.assertEqual(review.state, ReviewState.PENDING)
        self.assertEqual(review.body, "")
        self.assertIsNone(review.submitted_at)


class ReviewCommentTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.review.ReviewComment`
    """

    def test_from_json(self) -> None:
        """
        Test that the payload is parsed, including the diff anchoring
        (``path``, ``line``, ``diff_hunk``).
        """
        comment = ReviewComment.from_json(
            {
                "id": 10,
                "path": "src/app.py",
                "body": "Shouldn't this be a set?",
                "html_url": "https://github.com/octo/demo/pull/12#discussion_r10",
                "user": None,
                "line": 28,
                "diff_hunk": "@@ -16,33 +16,40 @@ def main():",
                "commit_id": "ecdd80bb57125d7ba9641ffaa4d7d2c19d3f3091",
                "created_at": "2026-08-14T17:17:52Z",
                "updated_at": "2026-08-14T17:17:52Z",
            }
        )

        self.assertEqual(comment.path, "src/app.py")
        self.assertEqual(comment.line, 28)
        self.assertEqual(comment.body, "Shouldn't this be a set?")

    def test_from_json_outdated(self) -> None:
        """
        Test that an outdated comment's null ``line`` stays ``None``.
        """
        comment = ReviewComment.from_json(
            {
                "id": 11,
                "path": "src/app.py",
                "body": "Old note",
                "html_url": "https://github.com/octo/demo/pull/12#discussion_r11",
                "line": None,
            }
        )

        self.assertIsNone(comment.line)
