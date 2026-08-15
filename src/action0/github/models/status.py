"""The commit status models (:py:class:`CombinedStatus`, :py:class:`CommitStatus`)."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import StrEnum
from typing import Any

from .timestamps import timestamp


class StatusState(StrEnum):
    """The state of a commit status (the *combined* state never says
    ``error`` — GitHub folds errors into ``failure`` there)."""

    ERROR = "error"
    FAILURE = "failure"
    PENDING = "pending"
    SUCCESS = "success"


@dataclass
class CommitStatus:
    """One commit status — a single context's verdict on a commit (the
    classic statuses API; check runs are the newer sibling)."""

    state: StatusState
    """The verdict."""

    context: str
    """The status name, e.g. ``"ci/jenkins"`` — one status per context,
    newer ones replace older ones."""

    description: str | None = None
    """The short explanation, if any."""

    target_url: str | None = None
    """The link to the full build output, if any."""

    created_at: datetime | None = None
    """When the status was first reported."""

    updated_at: datetime | None = None
    """When the status was last updated."""

    @classmethod
    def from_json(cls, data: Any) -> CommitStatus:
        """
        Build a status from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the status
        """
        return cls(
            state=StatusState(data["state"]),
            context=data["context"],
            description=data.get("description"),
            target_url=data.get("target_url"),
            created_at=timestamp(data.get("created_at")),
            updated_at=timestamp(data.get("updated_at")),
        )


@dataclass
class CombinedStatus:
    """
    The combined status of a commit — what
    :py:class:`~action0.github.operations.statuses.GetCombinedStatus`
    returns: one rolled-up state over all contexts, plus the individual
    statuses.
    """

    state: StatusState
    """The rolled-up verdict: ``success`` only when every context
    succeeded, ``pending`` when any is pending (or none exist)."""

    sha: str
    """The commit the statuses apply to."""

    total_count: int
    """The number of contexts."""

    statuses: list[CommitStatus] = field(default_factory=list)
    """The individual statuses, one per context."""

    @classmethod
    def from_json(cls, data: Any) -> CombinedStatus:
        """
        Build a combined status from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the combined status
        """
        return cls(
            state=StatusState(data["state"]),
            sha=data["sha"],
            total_count=data.get("total_count", 0),
            statuses=[CommitStatus.from_json(item) for item in data.get("statuses", [])],
        )
