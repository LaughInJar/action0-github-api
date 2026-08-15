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
from .pulls import CreatePull
from .pulls import GetPull
from .pulls import ListPulls
from .pulls import PullSort
from .pulls import PullStateFilter
from .repos import GetRepo
from .repos import ListOrgRepos
from .repos import ListUserRepos
from .repos import OrgRepoType
from .repos import RepoSort
from .repos import UserRepoType
from .search import RepoSearchSort
from .search import SearchOperation
from .search import SearchRepos
from .users import GetAuthenticatedUser
from .users import GetUser

__all__ = [
    "CreateIssue",
    "CreatePull",
    "GetAuthenticatedUser",
    "GetPull",
    "GetRepo",
    "GetUser",
    "GitHubOperation",
    "IssueSort",
    "IssueStateFilter",
    "ListIssues",
    "ListOrgRepos",
    "ListPulls",
    "ListUserRepos",
    "OrgRepoType",
    "PaginatedOperation",
    "PullSort",
    "PullStateFilter",
    "RepoSearchSort",
    "RepoSort",
    "SearchOperation",
    "SearchRepos",
    "SortDirection",
    "UserRepoType",
]
