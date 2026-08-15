"""The branch operations
(`GitHub docs <https://docs.github.com/en/rest/branches/branches>`__)."""

from __future__ import annotations

from typing import Any

from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.branch import Branch
from .base import GitHubOperation
from .base import PaginatedOperation


class ListBranches(PaginatedOperation[Branch]):
    """
    ``GET /repos/{owner}/{repo}/branches`` — list a repository's
    branches.

    The ``protected`` filter is the first boolean query parameter —
    sent web-style as ``true``/``false``:

    >>> operation = ListBranches(owner="python", repo="peps", protected=True)
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/peps/branches?per_page=30&page=1&protected=true'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/branches"

    owner: str = path_param()
    repo: str = path_param()

    protected: bool | None = query(default=None)
    """``True`` for only protected, ``False`` for only unprotected
    branches; ``None`` lists all."""

    def load_item(self, data: Any) -> Branch:
        """
        :param data: one decoded JSON array item
        :return: the branch
        """
        return Branch.from_json(data)


class GetBranch(GitHubOperation[Branch]):
    """
    ``GET /repos/{owner}/{repo}/branches/{branch}`` — fetch one branch,
    including the full tip commit the listings omit
    (:py:attr:`~action0.github.models.branch.Branch.commit`).

    >>> operation = GetBranch(owner="python", repo="peps", branch="main")
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/peps/branches/main'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/branches/{branch}"

    owner: str = path_param()
    repo: str = path_param()

    branch: str = path_param()
    """The branch name (slashes in names like ``feature/x`` are
    fine)."""

    def load_json(self, data: Any) -> Branch:
        """
        :param data: the decoded JSON payload
        :return: the branch
        """
        return Branch.from_json(data)
