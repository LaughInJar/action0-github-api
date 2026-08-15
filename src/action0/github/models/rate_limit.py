"""The rate limit models (:py:class:`RateLimitOverview`, :py:class:`RateLimit`)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from typing import Any


@dataclass
class RateLimit:
    """One rate limit window (of one resource category)."""

    limit: int
    """The requests allowed per window."""

    remaining: int
    """The requests left in the current window."""

    used: int
    """The requests already spent in the current window."""

    reset: datetime
    """When the window resets (GitHub sends this as epoch seconds —
    parsed into an aware UTC datetime)."""

    @classmethod
    def from_json(cls, data: Any) -> RateLimit:
        """
        Build one window from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the window
        """
        return cls(
            limit=data["limit"],
            remaining=data["remaining"],
            used=data.get("used", data["limit"] - data["remaining"]),
            reset=datetime.fromtimestamp(data["reset"], tz=timezone.utc),
        )


@dataclass
class RateLimitOverview:
    """
    The rate limit status across all resource categories.

    GitHub adds categories over time (``graphql``, ``code_search``,
    ``integration_manifest``, …), so everything lives in
    :py:attr:`resources` by name; the two everyone needs are also typed
    properties (:py:attr:`core`, :py:attr:`search`).
    """

    resources: dict[str, RateLimit]
    """All resource categories by name."""

    @property
    def core(self) -> RateLimit:
        """The core window — everything that is not one of the special
        categories, i.e. most REST calls."""
        return self.resources["core"]

    @property
    def search(self) -> RateLimit:
        """The search window (much smaller than core)."""
        return self.resources["search"]

    @classmethod
    def from_json(cls, data: Any) -> RateLimitOverview:
        """
        Build the overview from one decoded JSON object.

        The payload's legacy top-level ``rate`` key (a copy of
        ``resources.core``) is ignored — use :py:attr:`core`.

        :param data: the decoded JSON object
        :return: the overview
        """
        return cls(
            resources={
                name: RateLimit.from_json(window) for name, window in data["resources"].items()
            }
        )
