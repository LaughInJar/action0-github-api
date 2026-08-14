"""The repository operations (`GitHub docs <https://docs.github.com/en/rest/repos/repos>`__)."""

from __future__ import annotations

from typing import Any

from action0.client import path_param
from action0.req import Method

from ..models.repo import Repo
from .base import GitHubOperation


class GetRepo(GitHubOperation[Repo]):
    """
    ``GET /repos/{owner}/{repo}`` — fetch one repository.

    >>> GetRepo(owner="python", repo="cpython").as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/cpython'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}"

    owner: str = path_param()
    repo: str = path_param()

    def load_json(self, data: Any) -> Repo:
        """
        :param data: the decoded JSON payload
        :return: the repository
        """
        return Repo.from_json(data)
