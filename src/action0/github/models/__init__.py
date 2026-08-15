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
from .content import ContentFile
from .content import ContentType
from .content import DirectoryEntry
from .issue import Issue
from .issue import IssueState
from .label import Label
from .milestone import Milestone
from .org import Organization
from .page import Page
from .pull import MergeResult
from .pull import PullRequest
from .pull import PullRequestRef
from .rate_limit import RateLimit
from .rate_limit import RateLimitOverview
from .release import Release
from .release import ReleaseAsset
from .release import ReleaseNotes
from .repo import Repo
from .review import Review
from .review import ReviewComment
from .review import ReviewState
from .search import SearchPage
from .user import SimpleUser
from .user import User

__all__ = [
    "Commit",
    "CommitFile",
    "CommitFileStatus",
    "Comparison",
    "ComparisonStatus",
    "ContentFile",
    "ContentType",
    "DirectoryEntry",
    "GitIdentity",
    "Issue",
    "IssueComment",
    "IssueState",
    "Label",
    "MergeResult",
    "Milestone",
    "Organization",
    "Page",
    "PullRequest",
    "PullRequestRef",
    "RateLimit",
    "RateLimitOverview",
    "Release",
    "ReleaseAsset",
    "ReleaseNotes",
    "Repo",
    "Review",
    "ReviewComment",
    "ReviewState",
    "SearchPage",
    "SimpleUser",
    "User",
]
