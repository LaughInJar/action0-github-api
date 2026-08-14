"""
The GitHub endpoints as typed operation classes — one module per GitHub
resource area, one :py:class:`~action0.github.operations.base.GitHubOperation`
subclass per endpoint.
"""

from .base import GitHubOperation
from .repos import GetRepo
from .repos import ListOrgRepos
from .repos import ListUserRepos
from .repos import OrgRepoType
from .repos import RepoSort
from .repos import SortDirection
from .repos import UserRepoType

__all__ = [
    "GetRepo",
    "GitHubOperation",
    "ListOrgRepos",
    "ListUserRepos",
    "OrgRepoType",
    "RepoSort",
    "SortDirection",
    "UserRepoType",
]
