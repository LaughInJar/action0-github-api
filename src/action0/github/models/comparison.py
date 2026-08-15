"""The commit comparison model (:py:class:`Comparison`)."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import StrEnum
from typing import Any

from .commit import Commit
from .commit import CommitFile


class ComparisonStatus(StrEnum):
    """How ``head`` relates to ``base`` in a comparison."""

    DIVERGED = "diverged"
    AHEAD = "ahead"
    BEHIND = "behind"
    IDENTICAL = "identical"


@dataclass
class Comparison:
    """
    The comparison of two commits — what
    :py:class:`~action0.github.operations.commits.CompareCommits`
    returns: GitHub's three-dot comparison, i.e. ``head`` measured
    against the merge base (like ``git log base...head``), not against
    ``base`` itself.
    """

    status: ComparisonStatus
    """How ``head`` relates to ``base``."""

    ahead_by: int
    """How many commits ``head`` is ahead of the merge base."""

    behind_by: int
    """How many commits ``base`` is ahead of the merge base."""

    total_commits: int
    """The total number of commits ``head`` is ahead by — can exceed
    ``len(commits)``, which GitHub caps at 250."""

    html_url: str
    """The web URL of the comparison, e.g.
    ``"https://github.com/octo/demo/compare/main...topic"``."""

    merge_base_commit: Commit
    """The merge base — the common ancestor the comparison is measured
    from (the fork point)."""

    commits: list[Commit] = field(default_factory=list)
    """The commits ``head`` is ahead by, oldest first — capped at 250
    (:py:attr:`total_commits` has the real count; list the rest via
    :py:class:`~action0.github.operations.commits.ListCommits`)."""

    files: list[CommitFile] = field(default_factory=list)
    """The combined diff, file by file — capped at 300 files."""

    @classmethod
    def from_json(cls, data: Any) -> Comparison:
        """
        Build a comparison from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the comparison
        """
        return cls(
            status=ComparisonStatus(data["status"]),
            ahead_by=data["ahead_by"],
            behind_by=data["behind_by"],
            total_commits=data["total_commits"],
            html_url=data["html_url"],
            merge_base_commit=Commit.from_json(data["merge_base_commit"]),
            commits=[Commit.from_json(item) for item in data.get("commits", [])],
            files=[CommitFile.from_json(item) for item in data.get("files", [])],
        )
