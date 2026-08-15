"""The milestone operations
(`GitHub docs <https://docs.github.com/en/rest/issues/milestones>`__)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.milestone import Milestone
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
