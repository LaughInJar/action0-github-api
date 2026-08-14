import unittest

from action0.client import RetryingSyncBackend
from action0.client.testing import StubBackend
from action0.github import GitHubRetryPolicy
from action0.req import Request
from action0.req import Response

NOW = 1_000_000.0

RATE_LIMITED = Response(
    403,
    body='{"message": "API rate limit exceeded"}',
    headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(NOW + 90))},
)


def _clock() -> float:
    """
    :return: the fixed test time
    """
    return NOW


POLICY = GitHubRetryPolicy(clock=_clock)


class GitHubRetryPolicyTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.retry.GitHubRetryPolicy`
    """

    def test_rate_limited_403_is_retried(self) -> None:
        """
        Test that a 403 carrying rate-limit signals is retried — via
        ``x-ratelimit-remaining: 0`` or via ``Retry-After``.
        """
        request = Request("https://api.github.com/repos/python/cpython")
        secondary = Response(403, headers={"Retry-After": "60"})

        self.assertTrue(POLICY.should_retry_response(request, RATE_LIMITED, attempt=1))
        self.assertTrue(POLICY.should_retry_response(request, secondary, attempt=1))

    def test_plain_403_is_not_retried(self) -> None:
        """
        Test that a plain permission 403 (no rate-limit signals) is not
        retried.
        """
        request = Request("https://api.github.com/repos/python/cpython")

        self.assertFalse(POLICY.should_retry_response(request, Response(403), attempt=1))

    def test_rate_limited_403_respects_attempts_and_methods(self) -> None:
        """
        Test that the 403 handling keeps the base gates: no retry once
        the attempts are used up, and none for non-idempotent methods.
        """
        get_request = Request("https://api.github.com/repos/python/cpython")
        post_request = Request("https://api.github.com/repos/o/r/issues", method="POST")

        self.assertFalse(POLICY.should_retry_response(get_request, RATE_LIMITED, attempt=3))
        self.assertFalse(POLICY.should_retry_response(post_request, RATE_LIMITED, attempt=1))

    def test_transient_statuses_still_retry(self) -> None:
        """
        Test that the inherited transient statuses (e.g. 503) keep
        retrying.
        """
        request = Request("https://api.github.com/repos/python/cpython")

        self.assertTrue(POLICY.should_retry_response(request, Response(503), attempt=1))

    def test_delay_waits_until_rate_limit_reset(self) -> None:
        """
        Test that without a ``Retry-After`` the delay runs until
        ``x-ratelimit-reset``.
        """
        self.assertEqual(POLICY.delay_for(1, RATE_LIMITED), 90.0)

    def test_delay_reset_is_capped_at_max_backoff(self) -> None:
        """
        Test that a reset far in the future is capped at ``max_backoff``.
        """
        response = Response(
            403,
            headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(int(NOW + 3600))},
        )

        self.assertEqual(POLICY.delay_for(1, response), 120.0)
        self.assertEqual(
            GitHubRetryPolicy(clock=_clock, max_backoff=600.0).delay_for(1, response), 600.0
        )

    def test_retry_after_wins_over_reset(self) -> None:
        """
        Test that an explicit ``Retry-After`` beats the reset computation
        (GitHub's documented precedence).
        """
        response = Response(
            403,
            headers={
                "Retry-After": "60",
                "x-ratelimit-remaining": "0",
                "x-ratelimit-reset": str(int(NOW + 90)),
            },
        )

        self.assertEqual(POLICY.delay_for(1, response), 60.0)

    def test_delay_falls_back_to_backoff(self) -> None:
        """
        Test that without any rate-limit hints the base exponential
        backoff applies.
        """
        self.assertEqual(
            GitHubRetryPolicy(clock=_clock, jitter=False, backoff=0.5).delay_for(1, Response(503)),
            0.5,
        )

    def test_wrapped_backend_recovers_from_rate_limit(self) -> None:
        """
        Test the policy inside action0-client's retrying wrapper: a
        rate-limited 403 is waited out (per the reset header) and the
        second attempt succeeds.
        """
        naps: list[float] = []
        backend = RetryingSyncBackend(
            StubBackend(RATE_LIMITED, Response(200, body="ok")),
            POLICY,
            sleep=naps.append,
        )

        response = backend.send(Request("https://api.github.com/repos/python/cpython"))

        self.assertEqual(response.status, 200)
        self.assertEqual(naps, [90.0])
