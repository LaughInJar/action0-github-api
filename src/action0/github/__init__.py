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
from .conditional import GITHUB_CONDITIONAL_POLICY
from .conditional import ConditionalRequestsHook
from .models import Commit
from .models import CommitFile
from .models import CommitFileStatus
from .models import Comparison
from .models import ComparisonStatus
from .models import ContentFile
from .models import ContentType
from .models import DirectoryEntry
from .models import GitIdentity
from .models import Issue
from .models import IssueComment
from .models import IssueState
from .models import Label
from .models import MergeResult
from .models import Milestone
from .models import Organization
from .models import Page
from .models import PullRequest
from .models import PullRequestRef
from .models import RateLimit
from .models import RateLimitOverview
from .models import Release
from .models import ReleaseAsset
from .models import ReleaseNotes
from .models import Repo
from .models import Review
from .models import ReviewComment
from .models import ReviewState
from .models import SearchPage
from .models import SimpleUser
from .models import User
from .operations import GITHUB_UPLOADS_URL
from .operations import AddAssignees
from .operations import AddIssueLabels
from .operations import CompareCommits
from .operations import CreateIssue
from .operations import CreateIssueComment
from .operations import CreatePull
from .operations import CreatePullReview
from .operations import CreateRelease
from .operations import DeleteIssueComment
from .operations import DeleteRelease
from .operations import DownloadReleaseAsset
from .operations import GenerateReleaseNotes
from .operations import GetAuthenticatedUser
from .operations import GetCommit
from .operations import GetContent
from .operations import GetIssue
from .operations import GetLatestRelease
from .operations import GetOrg
from .operations import GetPull
from .operations import GetRateLimit
from .operations import GetReadme
from .operations import GetReleaseByTag
from .operations import GetRepo
from .operations import GetUser
from .operations import GitHubOperation
from .operations import IssueSearchSort
from .operations import IssueSort
from .operations import IssueStateFilter
from .operations import IssueStateReason
from .operations import ListCommits
from .operations import ListIssueComments
from .operations import ListIssues
from .operations import ListMilestones
from .operations import ListOrgMembers
from .operations import ListOrgRepos
from .operations import ListPullCommits
from .operations import ListPullFiles
from .operations import ListPullReviews
from .operations import ListPulls
from .operations import ListReleases
from .operations import ListRepoLabels
from .operations import ListReviewComments
from .operations import ListUserRepos
from .operations import LockIssue
from .operations import LockReason
from .operations import MergeMethod
from .operations import MergePull
from .operations import MilestoneSort
from .operations import NoContentOperation
from .operations import OrgMemberRole
from .operations import OrgRepoType
from .operations import PaginatedOperation
from .operations import PullSort
from .operations import PullStateFilter
from .operations import RemoveAssignees
from .operations import RemoveIssueLabel
from .operations import RepoSearchSort
from .operations import RepoSort
from .operations import ReviewEvent
from .operations import SearchIssues
from .operations import SearchOperation
from .operations import SearchRepos
from .operations import SearchUsers
from .operations import SortDirection
from .operations import UnlockIssue
from .operations import UpdateIssue
from .operations import UpdateIssueComment
from .operations import UpdatePull
from .operations import UpdateRelease
from .operations import UploadReleaseAsset
from .operations import UserRepoType
from .operations import UserSearchSort
from .pagination import all_items
from .pagination import all_items_async
from .pagination import all_items_deferred
from .retry import GitHubRetryPolicy

__version__: str = "0.1.0"

__all__ = [
    "AddAssignees",
    "AddIssueLabels",
    "Commit",
    "CommitFile",
    "CommitFileStatus",
    "CompareCommits",
    "Comparison",
    "ComparisonStatus",
    "ConditionalRequestsHook",
    "ContentFile",
    "ContentType",
    "CreateIssue",
    "CreateIssueComment",
    "CreatePull",
    "CreatePullReview",
    "CreateRelease",
    "DeleteIssueComment",
    "DeleteRelease",
    "DirectoryEntry",
    "DownloadReleaseAsset",
    "GITHUB_CONDITIONAL_POLICY",
    "GITHUB_UPLOADS_URL",
    "GenerateReleaseNotes",
    "GetAuthenticatedUser",
    "GetCommit",
    "GetContent",
    "GetIssue",
    "GetLatestRelease",
    "GetOrg",
    "GetPull",
    "GetRateLimit",
    "GetReadme",
    "GetReleaseByTag",
    "GetRepo",
    "GetUser",
    "GitHubClient",
    "GitHubOperation",
    "GitHubRetryPolicy",
    "GitIdentity",
    "Issue",
    "IssueComment",
    "IssueSearchSort",
    "IssueSort",
    "IssueState",
    "IssueStateFilter",
    "IssueStateReason",
    "Label",
    "ListCommits",
    "ListIssueComments",
    "ListIssues",
    "ListMilestones",
    "ListOrgMembers",
    "ListOrgRepos",
    "ListPullCommits",
    "ListPullFiles",
    "ListPullReviews",
    "ListPulls",
    "ListReleases",
    "ListRepoLabels",
    "ListReviewComments",
    "ListUserRepos",
    "LockIssue",
    "LockReason",
    "MergeMethod",
    "MergePull",
    "MergeResult",
    "Milestone",
    "MilestoneSort",
    "NoContentOperation",
    "OrgMemberRole",
    "OrgRepoType",
    "Organization",
    "Page",
    "PaginatedOperation",
    "PullRequest",
    "PullRequestRef",
    "PullSort",
    "PullStateFilter",
    "RateLimit",
    "RateLimitOverview",
    "Release",
    "ReleaseAsset",
    "ReleaseNotes",
    "RemoveAssignees",
    "RemoveIssueLabel",
    "Repo",
    "RepoSearchSort",
    "RepoSort",
    "Review",
    "ReviewComment",
    "ReviewEvent",
    "ReviewState",
    "SearchIssues",
    "SearchOperation",
    "SearchPage",
    "SearchRepos",
    "SearchUsers",
    "SimpleUser",
    "SortDirection",
    "UnlockIssue",
    "UpdateIssue",
    "UpdateIssueComment",
    "UpdatePull",
    "UpdateRelease",
    "UploadReleaseAsset",
    "User",
    "UserRepoType",
    "UserSearchSort",
    "all_items",
    "all_items_async",
    "all_items_deferred",
]
