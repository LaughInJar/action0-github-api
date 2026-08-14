"""
GitHub-aware retries (:py:class:`GitHubRetryPolicy`).

The mechanics come from action0-client: wrap any backend in the retrying
variant of its execution model
(:py:class:`~action0.client.retry.RetryingSyncBackend` /
:py:class:`~action0.client.retry.RetryingAsyncBackend` /
:py:class:`~action0.client.retry.RetryingDeferredBackend`) and hand it
this policy::

    backend = RetryingSyncBackend(RequestsBackend(), GitHubRetryPolicy())
    client = GitHubClient(backend, token="ghp_...")
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from action0.client import RetryPolicy
from action0.req import Request
from action0.req import Response

RATE_LIMIT_REMAINING = "x-ratelimit-remaining"
"""The response header counting the requests left in the rate window."""

RATE_LIMIT_RESET = "x-ratelimit-reset"
"""The response header naming the rate window's end (epoch seconds)."""


def _is_rate_limited(response: Response) -> bool:
    """
    Whether a response carries GitHub's rate-limit signals: a
    ``Retry-After`` header (secondary limits) or an exhausted
    ``x-ratelimit-remaining`` (primary limits).

    :param response: the response to inspect
    :return: whether GitHub says "rate limited"
    """
    if response.headers.get("Retry-After") is not None:
        return True
    return response.headers.get(RATE_LIMIT_REMAINING) == "0"


@dataclass(frozen=True)
class GitHubRetryPolicy(RetryPolicy):
    """
    A :py:class:`~action0.client.retry.RetryPolicy` tuned to the GitHub
    API. On top of the base behavior (transient 5xx/429 statuses,
    ``Retry-After`` honored, idempotent methods only — so ``CreateIssue``
    and friends are never blindly repeated) it knows GitHub's rate limits:

    - a **403 is retried only when it actually is a rate limit** (GitHub
      also answers plain permission problems with 403): a ``Retry-After``
      header or ``x-ratelimit-remaining: 0`` must be present,
    - without a ``Retry-After``, an exhausted primary rate limit is waited
      out until ``x-ratelimit-reset`` (GitHub's documented advice), capped
      at :py:attr:`max_backoff` — raise it if you want to sit out whole
      rate windows.

    Example — an exhausted rate window resetting 90 seconds from now:

    >>> policy = GitHubRetryPolicy(clock=lambda: 1_000_000.0)
    >>> headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1000090"}
    >>> policy.delay_for(1, Response(403, headers=headers))
    90.0
    """

    max_backoff: float = 120.0
    """The wait cap in seconds — higher than the base default so GitHub's
    "wait at least a minute" advice for secondary rate limits fits."""

    clock: Callable[[], float] = time.time
    """The epoch-seconds clock ``x-ratelimit-reset`` waits are computed
    against — injectable for tests."""

    def should_retry_response(self, request: Request, response: Response, attempt: int) -> bool:
        """
        The base statuses, plus 403 when the response says "rate limited".

        :param request: the request that was sent
        :param response: the response that arrived
        :param attempt: the (1-based) attempt that produced it
        :return: whether to retry
        """
        if super().should_retry_response(request, response, attempt):
            return True
        return (
            response.status == 403
            and attempt < self.attempts
            and self.applies_to(request)
            and _is_rate_limited(response)
        )

    def delay_for(self, attempt: int, response: Response | None = None) -> float:
        """
        The base delays (``Retry-After`` first, else jittered exponential
        backoff), with one addition: an exhausted primary rate limit
        without a ``Retry-After`` waits until ``x-ratelimit-reset``.

        :param attempt: the attempt that just failed
        :param response: the response that triggered the retry, if the
                         attempt produced one
        :return: the wait in seconds, capped at :py:attr:`max_backoff`
        """
        if (
            response is not None
            and self.respect_retry_after
            # an explicit Retry-After wins — the base handles it
            and response.headers.get("Retry-After") is None
        ):
            reset_wait = self._reset_wait(response)
            if reset_wait is not None:
                return min(self.max_backoff, max(0.0, reset_wait))
        return super().delay_for(attempt, response)

    def _reset_wait(self, response: Response) -> float | None:
        """
        The seconds until the rate window resets, if the response reports
        an exhausted window with a parseable reset time.

        :param response: the response to inspect
        :return: the wait, or ``None`` if this is no exhausted window
        """
        if response.headers.get(RATE_LIMIT_REMAINING) != "0":
            return None
        reset = response.headers.get(RATE_LIMIT_RESET)
        if reset is None:
            return None
        try:
            return float(reset) - self.clock()
        except ValueError:
            return None
