import unittest

from action0.github import CheckConclusion
from action0.github import CheckRun
from action0.github import CheckRunStatus


class CheckRunTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.check.CheckRun`
    """

    def test_from_json_completed(self) -> None:
        """
        Test a completed run: status and conclusion as their enums.
        """
        run = CheckRun.from_json(
            {
                "id": 4,
                "name": "build (3.12)",
                "status": "completed",
                "conclusion": "success",
                "head_sha": "6dcb09b5",
                "html_url": "https://github.com/octo/demo/runs/4",
                "started_at": "2026-08-15T10:00:00Z",
                "completed_at": "2026-08-15T10:05:00Z",
            }
        )

        self.assertEqual(run.status, CheckRunStatus.COMPLETED)
        self.assertEqual(run.conclusion, CheckConclusion.SUCCESS)
        assert run.completed_at is not None
        self.assertEqual(run.completed_at.minute, 5)

    def test_from_json_in_progress(self) -> None:
        """
        Test a running check: no conclusion yet.
        """
        run = CheckRun.from_json(
            {
                "id": 5,
                "name": "tests",
                "status": "in_progress",
                "conclusion": None,
                "head_sha": "6dcb09b5",
            }
        )

        self.assertEqual(run.status, CheckRunStatus.IN_PROGRESS)
        self.assertIsNone(run.conclusion)
        self.assertIsNone(run.completed_at)
