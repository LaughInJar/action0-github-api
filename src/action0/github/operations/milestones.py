"""The milestone operations
(`GitHub docs <https://docs.github.com/en/rest/issues/milestones>`__)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from action0.client import json_field
from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.issue import IssueState
from ..models.milestone import Milestone
from .base import GitHubOperation
from .base import NoContentOperation
from .base import PaginatedOperation
from .base import SortDirection
from .issues import IssueStateFilter


class MilestoneSort(StrEnum):
    """The sort orders of the milestone listing."""

    DUE_ON = "due_on"
    COMPLETENESS = "completeness"


class ListMilestones(PaginatedOperation[Milestone]):
    """
    ``GET /repos/{owner}/{repo}/milestones`` — list a repository's
    milestones. The state filter reuses the issue vocabulary
    (:py:class:`~action0.github.operations.issues.IssueStateFilter` —
    milestones know the same ``open``/``closed``/``all``).

    >>> operation = ListMilestones(owner="python", repo="peps", sort=MilestoneSort.DUE_ON)
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/peps/milestones?per_page=30&page=1&sort=due_on'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/milestones"

    owner: str = path_param()
    repo: str = path_param()

    state: IssueStateFilter | None = query(default=None)
    """The state filter; ``None`` uses GitHub's default (``open``)."""

    sort: MilestoneSort | None = query(default=None)
    """The sort order; ``None`` uses GitHub's default (``due_on``)."""

    direction: SortDirection | None = query(default=None)
    """The sort direction; ``None`` uses GitHub's default (``asc``)."""

    def load_item(self, data: Any) -> Milestone:
        """
        :param data: one decoded JSON array item
        :return: the milestone
        """
        return Milestone.from_json(data)


class CreateMilestone(GitHubOperation[Milestone]):
    """
    ``POST /repos/{owner}/{repo}/milestones`` — create a milestone
    (requires a token with write access).
    """

    method = Method.POST
    path = "/repos/{owner}/{repo}/milestones"

    owner: str = path_param()
    repo: str = path_param()

    title: str = json_field()
    """The title, e.g. ``"v1.0"``."""

    description: str | None = json_field(default=None)
    """The description, if any."""

    due_on: datetime | None = json_field(default=None)
    """The due date (serialized to ISO 8601 in the JSON body)."""

    def load_json(self, data: Any) -> Milestone:
        """
        :param data: the decoded JSON payload
        :return: the created milestone (with its server-assigned
                 number)
        """
        return Milestone.from_json(data)


class UpdateMilestone(GitHubOperation[Milestone]):
    """
    ``PATCH /repos/{owner}/{repo}/milestones/{milestone_number}`` —
    update a milestone. PATCH semantics: ``None`` fields stay
    untouched; closing is ``state=IssueState.CLOSED``.
    """

    method = Method.PATCH
    path = "/repos/{owner}/{repo}/milestones/{milestone_number}"

    owner: str = path_param()
    repo: str = path_param()

    milestone_number: int = path_param()
    """The milestone number (:py:attr:`Milestone.number
    <action0.github.models.milestone.Milestone.number>` — unique per
    repository, not the global id)."""

    title: str | None = json_field(default=None)
    """The new title; ``None`` keeps the current one."""

    state: IssueState | None = json_field(default=None)
    """Open or close the milestone; ``None`` keeps the state."""

    description: str | None = json_field(default=None)
    """The new description; ``None`` keeps the current one."""

    due_on: datetime | None = json_field(default=None)
    """The new due date; ``None`` keeps the current one."""

    def load_json(self, data: Any) -> Milestone:
        """
        :param data: the decoded JSON payload
        :return: the updated milestone
        """
        return Milestone.from_json(data)


class DeleteMilestone(NoContentOperation):
    """
    ``DELETE /repos/{owner}/{repo}/milestones/{milestone_number}`` —
    delete a milestone (its issues survive, unassigned). Answers
    ``204``.
    """

    method = Method.DELETE
    path = "/repos/{owner}/{repo}/milestones/{milestone_number}"

    owner: str = path_param()
    repo: str = path_param()

    milestone_number: int = path_param()
    """The milestone number (not the global id)."""
