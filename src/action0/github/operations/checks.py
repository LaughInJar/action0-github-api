"""The check run operations
(`GitHub docs <https://docs.github.com/en/rest/checks/runs>`__)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.check import CheckRun
from ..models.page import Page
from .base import PaginatedOperation


class CheckRunStatusFilter(StrEnum):
    """The status filter of :py:class:`ListCheckRunsForRef`."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ListCheckRunsForRef(PaginatedOperation[CheckRun]):
    """
    ``GET /repos/{owner}/{repo}/commits/{ref}/check-runs`` — list a
    commit's check runs (the Checks API — GitHub Actions and modern CI
    apps report here; the classic statuses live in
    :py:class:`~action0.github.operations.statuses.GetCombinedStatus`).

    The one listing whose payload is not a bare array: GitHub wraps it
    in a ``{total_count, check_runs}`` envelope, so :py:meth:`load_json`
    unwraps before the usual per-item parsing (pagination still runs on
    the ``Link`` header, like everywhere else).
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/commits/{ref}/check-runs"

    owner: str = path_param()
    repo: str = path_param()

    ref: str = path_param()
    """The commit to list checks for — a sha, branch or tag."""

    check_name: str | None = query(default=None)
    """Only runs of the check with this name; ``None`` lists all."""

    status: CheckRunStatusFilter | None = query(default=None)
    """Only runs in this lifecycle phase; ``None`` lists all."""

    def load_item(self, data: Any) -> CheckRun:
        """
        :param data: one item of the envelope's ``check_runs`` array
        :return: the check run
        """
        return CheckRun.from_json(data)

    def load_json(self, data: Any) -> Page[CheckRun]:
        """
        Unwrap GitHub's ``{total_count, check_runs}`` envelope into the
        usual page.

        :param data: the decoded JSON payload (the envelope)
        :return: the page, pagination not yet attached
        """
        return Page(items=[self.load_item(item) for item in data["check_runs"]])
