"""The rate limit operation (`GitHub docs <https://docs.github.com/en/rest/rate-limit>`__)."""

from __future__ import annotations

from typing import Any

from action0.req import Method

from ..models.rate_limit import RateLimitOverview
from .base import GitHubOperation


class GetRateLimit(GitHubOperation[RateLimitOverview]):
    """
    ``GET /rate_limit`` — the current rate limit status for the
    authenticated user (or the IP, without a token).

    This call itself does not count against any limit, so it is safe to
    check before a burst of requests — the proactive complement to
    :py:class:`~action0.github.retry.GitHubRetryPolicy`, which reacts
    once a limit hits.

    >>> GetRateLimit().as_request("https://api.github.com").url.as_str()
    'https://api.github.com/rate_limit'
    """

    method = Method.GET
    path = "/rate_limit"

    def load_json(self, data: Any) -> RateLimitOverview:
        """
        :param data: the decoded JSON payload
        :return: the overview across all resource categories
        """
        return RateLimitOverview.from_json(data)
