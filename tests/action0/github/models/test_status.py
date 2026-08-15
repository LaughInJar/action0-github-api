import unittest

from action0.github import CombinedStatus
from action0.github import StatusState


class CombinedStatusTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.status.CombinedStatus`
    """

    def test_from_json(self) -> None:
        """
        Test that the rolled-up state and the per-context statuses are
        parsed.
        """
        combined = CombinedStatus.from_json(
            {
                "state": "failure",
                "sha": "6dcb09b5",
                "total_count": 2,
                "statuses": [
                    {"state": "success", "context": "ci/build"},
                    {
                        "state": "failure",
                        "context": "ci/tests",
                        "description": "3 tests failed",
                        "target_url": "https://ci.example.com/1",
                    },
                ],
            }
        )

        self.assertEqual(combined.state, StatusState.FAILURE)
        self.assertEqual(combined.total_count, 2)
        self.assertEqual(
            [(s.context, s.state) for s in combined.statuses],
            [("ci/build", StatusState.SUCCESS), ("ci/tests", StatusState.FAILURE)],
        )
        self.assertEqual(combined.statuses[1].description, "3 tests failed")
