"""The label operations
(`GitHub docs <https://docs.github.com/en/rest/issues/labels>`__)."""

from __future__ import annotations

from typing import Any

from action0.client import json_field
from action0.client import path_param
from action0.req import Method

from ..models.label import Label
from .base import GitHubOperation
from .base import PaginatedOperation


class ListRepoLabels(PaginatedOperation[Label]):
    """
    ``GET /repos/{owner}/{repo}/labels`` — list a repository's labels.

    >>> operation = ListRepoLabels(owner="python", repo="peps")
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/peps/labels?per_page=30&page=1'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/labels"

    owner: str = path_param()
    repo: str = path_param()

    def load_item(self, data: Any) -> Label:
        """
        :param data: one decoded JSON array item
        :return: the label
        """
        return Label.from_json(data)


class AddIssueLabels(GitHubOperation[list[Label]]):
    """
    ``POST /repos/{owner}/{repo}/issues/{issue_number}/labels`` — add
    labels to an issue or pull request, keeping the existing ones
    (unlike :py:class:`~action0.github.operations.issues.UpdateIssue`'s
    ``labels``, which replaces the whole set). Labels that don't exist
    in the repository yet are created on the fly.
    """

    method = Method.POST
    path = "/repos/{owner}/{repo}/issues/{issue_number}/labels"

    owner: str = path_param()
    repo: str = path_param()
    issue_number: int = path_param()

    labels: list[str] = json_field()
    """The label names to add."""

    def load_json(self, data: Any) -> list[Label]:
        """
        :param data: the decoded JSON payload (an array)
        :return: the issue's complete label set after the addition
        """
        return [Label.from_json(item) for item in data]


class RemoveIssueLabel(GitHubOperation[list[Label]]):
    """
    ``DELETE /repos/{owner}/{repo}/issues/{issue_number}/labels/{name}``
    — remove one label from an issue or pull request. Unusually for a
    DELETE, GitHub answers with a body: the remaining label set.
    """

    method = Method.DELETE
    path = "/repos/{owner}/{repo}/issues/{issue_number}/labels/{name}"

    owner: str = path_param()
    repo: str = path_param()
    issue_number: int = path_param()

    name: str = path_param()
    """The label name to remove (spaces and unicode are fine — the
    path segment is percent-encoded)."""

    def load_json(self, data: Any) -> list[Label]:
        """
        :param data: the decoded JSON payload (an array)
        :return: the issue's remaining label set
        """
        return [Label.from_json(item) for item in data]
