"""The commit operations (`GitHub docs <https://docs.github.com/en/rest/commits/commits>`__)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.commit import Commit
from ..models.comparison import Comparison
from .base import GitHubOperation
from .base import PaginatedOperation


class ListCommits(PaginatedOperation[Commit]):
    """
    ``GET /repos/{owner}/{repo}/commits`` — list a repository's commits,
    newest first.

    The ``file_path`` filter is called ``path`` on the wire — that name
    would shadow the operation's own path template attribute, so the
    field carries a wire-name alias:

    >>> operation = ListCommits(owner="python", repo="peps", file_path="pep-0008.txt")
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/peps/commits?per_page=30&page=1&path=pep-0008.txt'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/commits"

    owner: str = path_param()
    repo: str = path_param()

    sha: str | None = query(default=None)
    """The sha, branch or tag to start listing from; ``None`` uses the
    repository's default branch."""

    file_path: str | None = query("path", default=None)
    """Only commits touching this file or directory path (sent as
    ``path`` — GitHub's parameter name, aliased here because ``path``
    is the operation's path template)."""

    author: str | None = query(default=None)
    """Only commits by this author — a GitHub login or an email
    address."""

    committer: str | None = query(default=None)
    """Only commits committed by this account — a GitHub login or an
    email address."""

    since: datetime | None = query(default=None)
    """Only commits authored at or after this time (serialized to
    ISO 8601)."""

    until: datetime | None = query(default=None)
    """Only commits authored at or before this time (serialized to
    ISO 8601)."""

    def load_item(self, data: Any) -> Commit:
        """
        :param data: one decoded JSON array item
        :return: the commit
        """
        return Commit.from_json(data)


class GetCommit(GitHubOperation[Commit]):
    """
    ``GET /repos/{owner}/{repo}/commits/{ref}`` — fetch one commit,
    including the diff statistics and files the listings omit
    (:py:attr:`~action0.github.models.commit.Commit.additions`,
    :py:attr:`~action0.github.models.commit.Commit.files`, …; GitHub
    caps ``files`` at 300 for very large commits).

    >>> operation = GetCommit(owner="octo", repo="demo", ref="6dcb09b5")
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/octo/demo/commits/6dcb09b5'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/commits/{ref}"

    owner: str = path_param()
    repo: str = path_param()

    ref: str = path_param()
    """The commit to fetch — a sha, branch name or tag name."""

    def load_json(self, data: Any) -> Commit:
        """
        :param data: the decoded JSON payload
        :return: the commit
        """
        return Commit.from_json(data)


class CompareCommits(GitHubOperation[Comparison]):
    """
    ``GET /repos/{owner}/{repo}/compare/{base}...{head}`` — compare two
    commits: GitHub's three-dot comparison, measuring ``head`` against
    the merge base (like ``git log base...head``).

    The endpoint's ``basehead`` path segment combines two refs — here
    they stay two typed fields, joined by the path template (for a
    cross-fork comparison, prefix the ref with the fork owner, e.g.
    ``head="octocat:topic"``):

    >>> operation = CompareCommits(owner="octo", repo="demo", base="main", head="topic")
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/octo/demo/compare/main...topic'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/compare/{base}...{head}"

    owner: str = path_param()
    repo: str = path_param()

    base: str = path_param()
    """The ref to measure against — a sha, branch or tag name."""

    head: str = path_param()
    """The ref with the changes — a sha, branch or tag name
    (``"owner:ref"`` for a fork)."""

    def load_json(self, data: Any) -> Comparison:
        """
        :param data: the decoded JSON payload
        :return: the comparison
        """
        return Comparison.from_json(data)
