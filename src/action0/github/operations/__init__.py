"""
The GitHub endpoints as typed operation classes — one module per GitHub
resource area, one :py:class:`~action0.github.operations.base.GitHubOperation`
subclass per endpoint.
"""

from .base import GitHubOperation
from .base import PaginatedOperation
from .base import SortDirection
from .issues import CreateIssue
from .issues import IssueSort
from .issues import IssueStateFilter
from .issues import ListIssues
from .repos import GetRepo
from .repos import ListOrgRepos
from .repos import ListUserRepos
from .repos import OrgRepoType
from .repos import RepoSort
from .repos import UserRepoType

__all__ = [
    "CreateIssue",
    "GetRepo",
    "GitHubOperation",
    "IssueSort",
    "IssueStateFilter",
    "ListIssues",
    "ListOrgRepos",
    "ListUserRepos",
    "OrgRepoType",
    "PaginatedOperation",
    "RepoSort",
    "SortDirection",
    "UserRepoType",
]
