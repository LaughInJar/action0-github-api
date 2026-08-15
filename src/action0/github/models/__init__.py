"""
The result models — plain dataclasses the operations hand to the
application, each with a ``from_json`` classmethod building it from the
decoded API payload. They cover the commonly used fields of the GitHub
schemas, not every last one.
"""

from .comment import IssueComment
from .commit import Commit
from .commit import CommitFile
from .commit import CommitFileStatus
from .commit import GitIdentity
from .comparison import Comparison
from .comparison import ComparisonStatus
from .issue import Issue
from .issue import IssueState
from .label import Label
from .page import Page
from .pull import PullRequest
from .pull import PullRequestRef
from .rate_limit import RateLimit
from .rate_limit import RateLimitOverview
from .release import Release
from .release import ReleaseAsset
from .repo import Repo
from .search import SearchPage
from .user import SimpleUser
from .user import User

__all__ = [
    "Commit",
    "CommitFile",
    "CommitFileStatus",
    "Comparison",
    "ComparisonStatus",
    "GitIdentity",
    "Issue",
    "IssueComment",
    "IssueState",
    "Label",
    "Page",
    "PullRequest",
    "PullRequestRef",
    "RateLimit",
    "RateLimitOverview",
    "Release",
    "ReleaseAsset",
    "Repo",
    "SearchPage",
    "SimpleUser",
    "User",
]
