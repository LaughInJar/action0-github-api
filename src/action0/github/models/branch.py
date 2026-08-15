"""The branch model (:py:class:`Branch`)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .commit import Commit


@dataclass
class Branch:
    """
    A repository branch: a name pinned to a commit.

    The listing payloads carry only the tip's sha; fetching one branch
    via :py:class:`~action0.github.operations.branches.GetBranch` fills
    :py:attr:`commit` with the full tip commit.
    """

    name: str
    """The branch name, e.g. ``"main"``."""

    sha: str
    """The sha of the branch tip."""

    protected: bool = False
    """Whether branch protection rules apply."""

    commit: Commit | None = None
    """The full tip commit (``None`` in listings — only
    :py:class:`~action0.github.operations.branches.GetBranch` payloads
    carry it)."""

    @classmethod
    def from_json(cls, data: Any) -> Branch:
        """
        Build a branch from one decoded JSON object.

        The listing sends ``commit`` as a bare ``{sha, url}`` pair, the
        single-branch endpoint as a full commit object — told apart by
        the nested ``commit`` key only the full object has.

        :param data: the decoded JSON object
        :return: the branch
        """
        commit = data["commit"]
        return cls(
            name=data["name"],
            sha=commit["sha"],
            protected=data.get("protected", False),
            commit=Commit.from_json(commit) if "commit" in commit else None,
        )
