"""The commit models (:py:class:`Commit`, :py:class:`GitCommit`,
:py:class:`GitIdentity`, :py:class:`CommitFile`)."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import StrEnum
from typing import Any

from .timestamps import timestamp
from .user import SimpleUser


class CommitFileStatus(StrEnum):
    """What happened to a file in a commit (or comparison) diff."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    RENAMED = "renamed"
    COPIED = "copied"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


@dataclass
class GitIdentity:
    """
    A git-level author or committer identity — the name/email/date triple
    recorded in the commit object itself, as opposed to the GitHub
    *account* GitHub matched to it (a
    :py:class:`~action0.github.models.user.SimpleUser`, which may not
    exist at all).
    """

    name: str
    """The name as recorded in the commit."""

    email: str
    """The email address as recorded in the commit."""

    date: datetime | None = None
    """When the commit was authored/committed."""

    @classmethod
    def from_json(cls, data: Any) -> GitIdentity:
        """
        Build an identity from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the identity
        """
        return cls(
            name=data["name"],
            email=data["email"],
            date=timestamp(data.get("date")),
        )


@dataclass
class GitCommit:
    """
    A git-level commit object — flat, with ``message`` and the
    identities at the top level. This is what the write endpoints (e.g.
    :py:class:`~action0.github.operations.contents.CreateOrUpdateFile`)
    return, as opposed to the API-level :py:class:`Commit` wrapper the
    listing/fetch endpoints use (which nests these fields under a
    ``commit`` key).
    """

    sha: str
    """The full commit sha."""

    message: str
    """The commit message."""

    html_url: str | None = None
    """The web URL of the commit."""

    author: GitIdentity | None = None
    """Who wrote the change."""

    committer: GitIdentity | None = None
    """Who committed it."""

    parents: list[str] = field(default_factory=list)
    """The parent commit shas."""

    @classmethod
    def from_json(cls, data: Any) -> GitCommit:
        """
        Build a git commit from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the commit
        """
        author = data.get("author")
        committer = data.get("committer")
        return cls(
            sha=data["sha"],
            message=data["message"],
            html_url=data.get("html_url"),
            author=GitIdentity.from_json(author) if author is not None else None,
            committer=GitIdentity.from_json(committer) if committer is not None else None,
            parents=[parent["sha"] for parent in data.get("parents", [])],
        )


@dataclass
class CommitFile:
    """One file of a commit (or comparison) diff."""

    filename: str
    """The file path within the repository."""

    status: CommitFileStatus
    """What happened to the file."""

    additions: int
    """The number of added lines."""

    deletions: int
    """The number of deleted lines."""

    changes: int
    """The number of changed lines (additions + deletions)."""

    patch: str | None = None
    """The unified diff of the file — ``None`` for binary files and
    oversized diffs."""

    previous_filename: str | None = None
    """The path the file was renamed from (only on
    :py:attr:`~CommitFileStatus.RENAMED` files)."""

    @classmethod
    def from_json(cls, data: Any) -> CommitFile:
        """
        Build a diff file from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the diff file
        """
        return cls(
            filename=data["filename"],
            status=CommitFileStatus(data["status"]),
            additions=data["additions"],
            deletions=data["deletions"],
            changes=data["changes"],
            patch=data.get("patch"),
            previous_filename=data.get("previous_filename"),
        )


@dataclass
class Commit:
    """
    A commit as GitHub's API presents it.

    This is GitHub's ``commit`` schema, reduced to the commonly used
    fields and flattened: the nested ``commit`` object's message and git
    identities live directly on this class. The listing endpoints omit
    the diff statistics and files — those fields stay ``None`` here until
    the commit is fetched individually via
    :py:class:`~action0.github.operations.commits.GetCommit`.
    """

    sha: str
    """The full commit sha."""

    html_url: str
    """The web URL, e.g.
    ``"https://github.com/octo/demo/commit/6dcb09b5..."``."""

    message: str
    """The commit message."""

    git_author: GitIdentity | None = None
    """Who wrote the change, as recorded in the commit object."""

    git_committer: GitIdentity | None = None
    """Who committed it, as recorded in the commit object."""

    author: SimpleUser | None = None
    """The GitHub account matched to the author email — ``None`` when
    the email does not map to any account."""

    committer: SimpleUser | None = None
    """The GitHub account matched to the committer email (``None`` when
    unmatched; web commits show as the ``web-flow`` bot account)."""

    parents: list[str] = field(default_factory=list)
    """The parent commit shas (more than one on merge commits, none on
    an initial commit)."""

    additions: int | None = None
    """The number of added lines (``None`` in listings — only
    :py:class:`~action0.github.operations.commits.GetCommit` payloads
    carry the diff statistics)."""

    deletions: int | None = None
    """The number of deleted lines (``None`` in listings)."""

    files: list[CommitFile] | None = None
    """The diff, file by file (``None`` in listings)."""

    @classmethod
    def from_json(cls, data: Any) -> Commit:
        """
        Build a commit from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the commit
        """
        detail = data["commit"]
        git_author = detail.get("author")
        git_committer = detail.get("committer")
        author = data.get("author")
        committer = data.get("committer")
        stats = data.get("stats")
        files = data.get("files")
        return cls(
            sha=data["sha"],
            html_url=data["html_url"],
            message=detail["message"],
            git_author=GitIdentity.from_json(git_author) if git_author is not None else None,
            git_committer=(
                GitIdentity.from_json(git_committer) if git_committer is not None else None
            ),
            author=SimpleUser.from_json(author) if author is not None else None,
            committer=SimpleUser.from_json(committer) if committer is not None else None,
            parents=[parent["sha"] for parent in data.get("parents", [])],
            additions=stats["additions"] if stats is not None else None,
            deletions=stats["deletions"] if stats is not None else None,
            files=[CommitFile.from_json(item) for item in files] if files is not None else None,
        )
