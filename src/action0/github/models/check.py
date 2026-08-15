"""The check run model (:py:class:`CheckRun`)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from .timestamps import timestamp


class CheckRunStatus(StrEnum):
    """The lifecycle phase of a check run."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WAITING = "waiting"
    REQUESTED = "requested"
    PENDING = "pending"


class CheckConclusion(StrEnum):
    """The verdict of a completed check run."""

    SUCCESS = "success"
    FAILURE = "failure"
    NEUTRAL = "neutral"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"
    ACTION_REQUIRED = "action_required"
    STALE = "stale"


@dataclass
class CheckRun:
    """
    A check run — one entry of a commit's checks tab (the Checks API,
    what GitHub Actions and modern CI apps report through; the classic
    statuses are :py:class:`~action0.github.models.status.CommitStatus`).
    """

    id: int
    """The numeric check run id (globally unique)."""

    name: str
    """The check name, e.g. ``"build (3.12)"``."""

    status: CheckRunStatus
    """The lifecycle phase."""

    head_sha: str
    """The commit the check ran against."""

    conclusion: CheckConclusion | None = None
    """The verdict — ``None`` until the run is
    :py:attr:`~CheckRunStatus.COMPLETED`."""

    html_url: str | None = None
    """The web URL of the run."""

    details_url: str | None = None
    """The reporting app's own results page, if any."""

    started_at: datetime | None = None
    """When the run started."""

    completed_at: datetime | None = None
    """When the run completed (``None`` while in progress)."""

    @classmethod
    def from_json(cls, data: Any) -> CheckRun:
        """
        Build a check run from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the check run
        """
        conclusion = data.get("conclusion")
        return cls(
            id=data["id"],
            name=data["name"],
            status=CheckRunStatus(data["status"]),
            head_sha=data["head_sha"],
            conclusion=CheckConclusion(conclusion) if conclusion is not None else None,
            html_url=data.get("html_url"),
            details_url=data.get("details_url"),
            started_at=timestamp(data.get("started_at")),
            completed_at=timestamp(data.get("completed_at")),
        )
