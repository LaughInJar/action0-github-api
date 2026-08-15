"""
The result models — plain dataclasses the operations hand to the
application, each with a ``from_json`` classmethod building it from the
decoded API payload. They cover the commonly used fields of the GitHub
schemas, not every last one.
"""

from .comment import IssueComment
from .issue import Issue
from .issue import IssueState
from .label import Label
from .page import Page
from .pull import PullRequest
from .pull import PullRequestRef
from .repo import Repo
from .search import SearchPage
from .user import SimpleUser
from .user import User

__all__ = [
    "Issue",
    "IssueComment",
    "IssueState",
    "Label",
    "Page",
    "PullRequest",
    "PullRequestRef",
    "Repo",
    "SearchPage",
    "SimpleUser",
    "User",
]
