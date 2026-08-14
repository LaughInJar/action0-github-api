"""
The result models — plain dataclasses the operations hand to the
application, each with a ``from_json`` classmethod building it from the
decoded API payload. They cover the commonly used fields of the GitHub
schemas, not every last one.
"""

from .issue import Issue
from .issue import IssueState
from .label import Label
from .page import Page
from .repo import Repo
from .user import SimpleUser
from .user import User

__all__ = [
    "Issue",
    "IssueState",
    "Label",
    "Page",
    "Repo",
    "SimpleUser",
    "User",
]
