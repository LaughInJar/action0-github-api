"""The commit status operations
(`GitHub docs <https://docs.github.com/en/rest/commits/statuses>`__)."""

from __future__ import annotations

from typing import Any

from action0.client import path_param
from action0.req import Method

from ..models.status import CombinedStatus
from .base import GitHubOperation


class GetCombinedStatus(GitHubOperation[CombinedStatus]):
    """
    ``GET /repos/{owner}/{repo}/commits/{ref}/status`` — the rolled-up
    commit status: one state over all contexts, plus the individual
    statuses. The classic pre-merge gate — pair it with
    :py:class:`~action0.github.operations.checks.ListCheckRunsForRef`,
    which covers the newer Checks API (GitHub Actions reports there,
    not here).

    >>> operation = GetCombinedStatus(owner="octo", repo="demo", ref="main")
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/octo/demo/commits/main/status'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/commits/{ref}/status"

    owner: str = path_param()
    repo: str = path_param()

    ref: str = path_param()
    """The commit to check — a sha, branch or tag."""

    def load_json(self, data: Any) -> CombinedStatus:
        """
        :param data: the decoded JSON payload
        :return: the combined status
        """
        return CombinedStatus.from_json(data)
