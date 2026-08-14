"""
A fully typed GitHub REST API client built on action0-client.

GitHub endpoints are described as typed
:py:class:`~action0.github.operations.base.GitHubOperation` dataclasses
(in :py:mod:`action0.github.operations`, one module per resource area),
their results as plain dataclasses (in :py:mod:`action0.github.models`),
and :py:class:`~action0.github.client.GitHubClient` sends them. Which
execution model runs them — synchronous, asyncio or Twisted — is decided
by the :py:class:`~action0.client.backend.Backend` you plug in, and the
static types follow it.
"""

from .client import GitHubClient
from .models import Issue
from .models import IssueState
from .models import Label
from .models import Page
from .models import Repo
from .models import SearchPage
from .models import SimpleUser
from .models import User
from .operations import CreateIssue
from .operations import GetAuthenticatedUser
from .operations import GetRepo
from .operations import GetUser
from .operations import GitHubOperation
from .operations import IssueSort
from .operations import IssueStateFilter
from .operations import ListIssues
from .operations import ListOrgRepos
from .operations import ListUserRepos
from .operations import OrgRepoType
from .operations import PaginatedOperation
from .operations import RepoSearchSort
from .operations import RepoSort
from .operations import SearchOperation
from .operations import SearchRepos
from .operations import SortDirection
from .operations import UserRepoType
from .pagination import all_items
from .pagination import all_items_async
from .pagination import all_items_deferred
from .retry import GitHubRetryPolicy

__version__: str = "0.1.0"

__all__ = [
    "CreateIssue",
    "GetAuthenticatedUser",
    "GetRepo",
    "GetUser",
    "GitHubClient",
    "GitHubOperation",
    "GitHubRetryPolicy",
    "Issue",
    "IssueSort",
    "IssueState",
    "IssueStateFilter",
    "Label",
    "ListIssues",
    "ListOrgRepos",
    "ListUserRepos",
    "OrgRepoType",
    "Page",
    "PaginatedOperation",
    "Repo",
    "RepoSearchSort",
    "RepoSort",
    "SearchOperation",
    "SearchPage",
    "SearchRepos",
    "SimpleUser",
    "SortDirection",
    "User",
    "UserRepoType",
    "all_items",
    "all_items_async",
    "all_items_deferred",
]
