"""The pull request models (:py:class:`PullRequest`, :py:class:`PullRequestRef`,
:py:class:`MergeResult`)."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any

from .issue import IssueState
from .label import Label
from .repo import Repo
from .timestamps import timestamp
from .user import SimpleUser


@dataclass
class PullRequestRef:
    """
    One side of a pull request — its ``head`` (the proposed changes) or
    ``base`` (where they should be merged): a branch pinned to a commit.
    """

    label: str
    """Owner and branch, e.g. ``"octocat:new-topic"``."""

    ref: str
    """The branch name, e.g. ``"new-topic"``."""

    sha: str
    """The commit the ref pointed to when GitHub built the payload."""

    user: SimpleUser | None = None
    """The owner of the repository the ref lives in (``None`` e.g. for
    deleted accounts)."""

    repo: Repo | None = None
    """The repository the ref lives in (``None`` when a fork was
    deleted after the pull request was opened)."""

    @classmethod
    def from_json(cls, data: Any) -> PullRequestRef:
        """
        Build a ref from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the ref
        """
        user = data.get("user")
        repo = data.get("repo")
        return cls(
            label=data["label"],
            ref=data["ref"],
            sha=data["sha"],
            user=SimpleUser.from_json(user) if user is not None else None,
            repo=Repo.from_json(repo) if repo is not None else None,
        )


@dataclass
class MergeResult:
    """
    What :py:class:`~action0.github.operations.pulls.MergePull` returns
    on success. (An unmergeable pull request is not a result but an
    error — GitHub answers 405/409, which raise
    :py:class:`~action0.client.errors.APIError`.)
    """

    sha: str
    """The sha of the merge commit."""

    merged: bool
    """Whether the pull request was merged (always ``True`` on the
    success payload — kept for fidelity with GitHub's schema)."""

    message: str
    """GitHub's human-readable outcome message."""

    @classmethod
    def from_json(cls, data: Any) -> MergeResult:
        """
        Build a merge result from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the merge result
        """
        return cls(sha=data["sha"], merged=data["merged"], message=data["message"])


@dataclass
class PullRequest:
    """
    A GitHub pull request.

    This is GitHub's ``pull-request`` schema, reduced to the commonly
    used fields. The listing endpoints send a slimmer variant
    (``pull-request-simple``) without the merge/diff statistics — those
    fields stay ``None`` here until the pull request is fetched
    individually.
    """

    id: int
    """The numeric pull request id (globally unique)."""

    number: int
    """The pull request number (unique per repository, shared with the
    issue numbering), e.g. ``1347``."""

    title: str
    """The title."""

    state: IssueState
    """Whether the pull request is open or closed (a pull request *is*
    an issue, and shares its two-state vocabulary — "merged" is not a
    state but :py:attr:`is_merged`, i.e. closed with a
    :py:attr:`merged_at` timestamp)."""

    html_url: str
    """The web URL, e.g. ``"https://github.com/python/cpython/pull/1"``."""

    head: PullRequestRef
    """The proposed changes: branch and commit they come from."""

    base: PullRequestRef
    """Where the changes should be merged into."""

    user: SimpleUser | None = None
    """The author (``None`` e.g. for deleted accounts)."""

    body: str | None = None
    """The description text, if any."""

    labels: list[Label] = field(default_factory=list)
    """The labels."""

    assignees: list[SimpleUser] = field(default_factory=list)
    """The assigned users."""

    requested_reviewers: list[SimpleUser] = field(default_factory=list)
    """The users whose review is (still) requested — GitHub removes a
    reviewer from this list once they review."""

    draft: bool = False
    """Whether the pull request is a draft."""

    locked: bool = False
    """Whether the conversation is locked."""

    merge_commit_sha: str | None = None
    """The sha of the (test) merge commit, if GitHub computed one."""

    mergeable: bool | None = None
    """Whether the branch merges cleanly — ``None`` in listings and
    while GitHub is still computing it (only :py:class:`GetPull
    <action0.github.operations.pulls.GetPull>` payloads carry it)."""

    commits: int | None = None
    """The number of commits (``None`` in listings — only
    :py:class:`~action0.github.operations.pulls.GetPull` payloads
    carry the diff statistics)."""

    additions: int | None = None
    """The number of added lines (``None`` in listings)."""

    deletions: int | None = None
    """The number of deleted lines (``None`` in listings)."""

    changed_files: int | None = None
    """The number of changed files (``None`` in listings)."""

    created_at: datetime | None = None
    """When the pull request was opened."""

    updated_at: datetime | None = None
    """When the pull request was last updated."""

    closed_at: datetime | None = None
    """When the pull request was closed (``None`` while it is open)."""

    merged_at: datetime | None = None
    """When the pull request was merged (``None`` if it was not)."""

    @property
    def is_merged(self) -> bool:
        """Whether the pull request was merged — GitHub's own signal is
        the presence of :py:attr:`merged_at` (a merged pull request is
        always ``closed``, so :py:attr:`state` cannot tell)."""
        return self.merged_at is not None

    @classmethod
    def from_json(cls, data: Any) -> PullRequest:
        """
        Build a pull request from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the pull request
        """
        user = data.get("user")
        return cls(
            id=data["id"],
            number=data["number"],
            title=data["title"],
            state=IssueState(data["state"]),
            html_url=data["html_url"],
            head=PullRequestRef.from_json(data["head"]),
            base=PullRequestRef.from_json(data["base"]),
            user=SimpleUser.from_json(user) if user is not None else None,
            body=data.get("body"),
            labels=[Label.from_json(item) for item in data.get("labels", [])],
            assignees=[SimpleUser.from_json(item) for item in data.get("assignees", [])],
            requested_reviewers=[
                SimpleUser.from_json(item) for item in data.get("requested_reviewers", [])
            ],
            draft=data.get("draft", False),
            locked=data.get("locked", False),
            merge_commit_sha=data.get("merge_commit_sha"),
            mergeable=data.get("mergeable"),
            commits=data.get("commits"),
            additions=data.get("additions"),
            deletions=data.get("deletions"),
            changed_files=data.get("changed_files"),
            created_at=timestamp(data.get("created_at")),
            updated_at=timestamp(data.get("updated_at")),
            closed_at=timestamp(data.get("closed_at")),
            merged_at=timestamp(data.get("merged_at")),
        )
