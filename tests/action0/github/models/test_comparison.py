import unittest

from action0.github import Comparison
from action0.github import ComparisonStatus

COMMIT_PAYLOAD = {
    "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
    "html_url": "https://github.com/octo/demo/commit/6dcb09b5b57875f334f61aebed695e2e4193db5e",
    "commit": {"message": "Fix all the bugs"},
    "parents": [],
}

COMPARISON_PAYLOAD = {
    "status": "ahead",
    "ahead_by": 2,
    "behind_by": 0,
    "total_commits": 2,
    "html_url": "https://github.com/octo/demo/compare/main...topic",
    "merge_base_commit": COMMIT_PAYLOAD,
    "commits": [COMMIT_PAYLOAD, COMMIT_PAYLOAD],
    "files": [
        {
            "filename": "README.md",
            "status": "modified",
            "additions": 5,
            "deletions": 1,
            "changes": 6,
        }
    ],
}


class ComparisonTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.comparison.Comparison`
    """

    def test_from_json(self) -> None:
        """
        Test that the payload is parsed: status as the enum, the counts,
        the commits and the combined diff.
        """
        comparison = Comparison.from_json(COMPARISON_PAYLOAD)

        self.assertEqual(comparison.status, ComparisonStatus.AHEAD)
        self.assertEqual(comparison.ahead_by, 2)
        self.assertEqual(comparison.behind_by, 0)
        self.assertEqual(comparison.total_commits, 2)
        self.assertEqual(comparison.merge_base_commit.message, "Fix all the bugs")
        self.assertEqual(len(comparison.commits), 2)
        self.assertEqual(comparison.files[0].filename, "README.md")

    def test_from_json_minimal_commit(self) -> None:
        """
        Test that a commit payload without git identities (only the
        ``message`` inside the nested ``commit`` object) parses — the
        identity fields stay ``None``.
        """
        comparison = Comparison.from_json(COMPARISON_PAYLOAD)

        self.assertIsNone(comparison.merge_base_commit.git_author)
        self.assertIsNone(comparison.merge_base_commit.author)
        self.assertEqual(comparison.merge_base_commit.parents, [])
