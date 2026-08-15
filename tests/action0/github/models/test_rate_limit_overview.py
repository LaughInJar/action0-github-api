import unittest
from datetime import datetime
from datetime import timezone

from action0.github import RateLimit
from action0.github import RateLimitOverview

WINDOW_PAYLOAD = {
    "limit": 5000,
    "remaining": 4999,
    "used": 1,
    "reset": 1755264000,  # 2026-08-15T13:20:00Z as epoch seconds
}

OVERVIEW_PAYLOAD = {
    "resources": {
        "core": WINDOW_PAYLOAD,
        "search": {"limit": 30, "remaining": 18, "used": 12, "reset": 1755264000},
        "code_search": {"limit": 10, "remaining": 10, "used": 0, "reset": 1755264000},
    },
    "rate": WINDOW_PAYLOAD,  # the legacy top-level copy of resources.core
}


class RateLimitTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.rate_limit.RateLimit`
    """

    def test_from_json(self) -> None:
        """
        Test that a window payload is mapped onto the dataclass — with
        the epoch-seconds ``reset`` parsed into an aware UTC datetime.
        """
        window = RateLimit.from_json(WINDOW_PAYLOAD)

        self.assertEqual(window.limit, 5000)
        self.assertEqual(window.remaining, 4999)
        self.assertEqual(window.used, 1)
        self.assertEqual(window.reset, datetime.fromtimestamp(1755264000, tz=timezone.utc))
        self.assertEqual(window.reset.tzinfo, timezone.utc)

    def test_from_json_without_used(self) -> None:
        """
        Test that a missing ``used`` is derived from limit − remaining.
        """
        window = RateLimit.from_json({"limit": 30, "remaining": 18, "reset": 1755264000})

        self.assertEqual(window.used, 12)


class RateLimitOverviewTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.rate_limit.RateLimitOverview`
    """

    def test_from_json(self) -> None:
        """
        Test that every resource category lands in ``resources`` —
        including ones this library doesn't know by name — and that the
        ``core``/``search`` conveniences point into it.
        """
        overview = RateLimitOverview.from_json(OVERVIEW_PAYLOAD)

        self.assertEqual(sorted(overview.resources), ["code_search", "core", "search"])
        self.assertEqual(overview.core.limit, 5000)
        self.assertEqual(overview.search.remaining, 18)
        self.assertEqual(overview.resources["code_search"].limit, 10)
