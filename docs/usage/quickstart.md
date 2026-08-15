# Quickstart

## Installation

Pick the extra matching the HTTP backend you want to run on — it pulls in
the corresponding extra of
[action0-client](https://laughinjar.github.io/action0-client/) (the stdlib
`urllib` and thread-pool backends need no extra):

```shell
uv add "action0-github-api[httpx]"     # or [requests], [aiohttp], [urllib3], [twisted], [all]
```

## The first request

A {py:class}`~action0.github.client.GitHubClient` plus an operation is all
it takes. Without a token, public data works at 60 requests/hour:

```python
from action0.client.backends.requests import RequestsBackend
from action0.github import GetRepo, GitHubClient

with RequestsBackend() as backend:
    client = GitHubClient(backend)
    repo = client.send(GetRepo(owner="python", repo="cpython"))  # a Repo
    print(repo.full_name, repo.language, repo.stargazers_count)
```

The same operation on asyncio — only the backend changes, and `send()`
now returns an awaitable (the type checker knows):

```python
from action0.client.backends.httpx import AsyncHttpxBackend
from action0.github import GetRepo, GitHubClient

async with AsyncHttpxBackend() as backend:
    client = GitHubClient(backend)
    repo = await client.send(GetRepo(owner="python", repo="cpython"))  # Awaitable[Repo]
```

— or on Twisted, as a `Deferred[Repo]`:

```python
from action0.client.backends.twisted import TwistedBackend
from action0.github import GetRepo, GitHubClient

client = GitHubClient(TwistedBackend())
deferred = client.send(GetRepo(owner="python", repo="cpython"))  # Deferred[Repo]
deferred.addCallback(lambda repo: print(repo.full_name))
```

`examples/get_repo.py` in the repository shows all three side by side and
a runnable, network-free demo.

## Listing repositories

{py:class}`~action0.github.operations.repos.ListOrgRepos` and
{py:class}`~action0.github.operations.repos.ListUserRepos` show the query
side: every filter value is an enum — your IDE completes the legal values,
no GitHub docs lookup needed — and a `None` filter is simply not sent,
falling back to GitHub's default:

```python
from action0.github import ListOrgRepos, RepoSort, SortDirection

repos = client.send(  # a Page[Repo] — sequence-like, iterate away
    ListOrgRepos(org="python", sort=RepoSort.PUSHED, direction=SortDirection.DESC, per_page=10)
)
```

## Pagination

Listings return a {py:class}`~action0.github.models.page.Page`: it
behaves like the list of its items, and its `next` attribute is the
ready-to-send operation for the following page — present exactly when
the response's `Link` header announced one, `None` on the last page.
Pagination is plain data, so it works identically in every execution
model:

```python
page = client.send(ListOrgRepos(org="python"))  # or await, or as a Deferred
while True:
    for repo in page:
        ...
    if page.next is None:
        break
    page = client.send(page.next)
```

The flattening helpers spare you the loop — one per execution model.
`all_items` (sync) and `all_items_async` fetch pages lazily as the
iteration proceeds; `all_items_deferred` gathers everything into one
list (a Deferred cannot stream). Each page is one API request — mind
the rate limit on huge listings:

```python
from action0.github import all_items, all_items_async, all_items_deferred

for repo in all_items(client, ListOrgRepos(org="python")):  # sync
    ...
async for repo in all_items_async(client, ListOrgRepos(org="python")):  # asyncio
    ...
deferred = all_items_deferred(client, ListOrgRepos(org="python"))  # Twisted: Deferred[list[Repo]]
```

## Searching

{py:class}`~action0.github.operations.search.SearchRepos` takes GitHub's
[query syntax](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories)
and returns a {py:class}`~action0.github.models.search.SearchPage` — a
`Page` plus the search envelope (`total_count`, `incomplete_results`).
It paginates like the listings (`next`, or the `all_items` helpers;
GitHub caps search results at 1000 items):

```python
from action0.github import RepoSearchSort, SearchRepos

hits = client.send(SearchRepos(q="http client language:python", sort=RepoSearchSort.STARS))
print(hits.total_count, [r.full_name for r in hits])
```

{py:class}`~action0.github.operations.search.SearchIssues` and
{py:class}`~action0.github.operations.search.SearchUsers` work the
same way. Issue search returns pull requests too — filter with
`is:issue`/`is:pr` in the query or via `is_pull_request` after the
fact; user search hits carry only the embedded-user fields
(`SimpleUser`), so follow up with `GetUser` for a full profile:

```python
from action0.github import IssueSearchSort, SearchIssues, SearchUsers, UserSearchSort

bugs = client.send(
    SearchIssues(q="repo:python/cpython is:open label:bug", sort=IssueSearchSort.REACTIONS)
)
users = client.send(SearchUsers(q="fullname:Guido type:user", sort=UserSearchSort.FOLLOWERS))
```

## Working with issues

{py:class}`~action0.github.operations.issues.ListIssues` filters the same
way (note: GitHub returns pull requests here too — every pull request is
an issue — so filter via `is_pull_request`):

```python
from action0.github import IssueStateFilter, ListIssues

issues = client.send(ListIssues(owner="python", repo="peps", state=IssueStateFilter.OPEN))
real_issues = [i for i in issues if not i.is_pull_request]  # one Page — follow .next for more
```

{py:class}`~action0.github.operations.issues.CreateIssue` is the first
write operation: its non-path fields become the JSON request body
(`None` fields are omitted), and it needs a token with write access:

```python
from action0.github import CreateIssue

issue = client.send(CreateIssue(owner="octo", repo="demo", title="Found a bug", labels=["bug"]))
print(issue.number, issue.html_url)  # the server-assigned number and URL
```

{py:class}`~action0.github.operations.issues.GetIssue` fetches one
issue by number, and
{py:class}`~action0.github.operations.issues.UpdateIssue` is the first
PATCH operation: only the fields you set are changed — a `None` field
is omitted from the body and leaves the issue untouched (so closing an
issue does not blank its title). Being non-idempotent, a PATCH is
never blindly repeated by the retry policy:

```python
from action0.github import GetIssue, IssueState, IssueStateReason, UpdateIssue

issue = client.send(GetIssue(owner="octo", repo="demo", issue_number=1347))
issue = client.send(
    UpdateIssue(
        owner="octo",
        repo="demo",
        issue_number=1347,
        state=IssueState.CLOSED,
        state_reason=IssueStateReason.NOT_PLANNED,
    )
)
print(issue.state)  # IssueState.CLOSED
```

Comments work on issues and pull requests alike (a pull request's
conversation *is* its issue's comment thread):

```python
from action0.github import CreateIssueComment, ListIssueComments

comments = client.send(ListIssueComments(owner="octo", repo="demo", issue_number=1347))
print([c.user.login for c in comments if c.user])  # one Page — follow .next for more

comment = client.send(
    CreateIssueComment(owner="octo", repo="demo", issue_number=1347, body="Fixed in v2.")
)
print(comment.html_url)
```

Editing and deleting address a comment by its *id* (repository-global —
no issue number in the path).
{py:class}`~action0.github.operations.issues.DeleteIssueComment` is a
**no-content** operation: GitHub answers `204` and `send` yields plain
`None`. Locking a conversation works the same way:

```python
from action0.github import DeleteIssueComment, LockIssue, LockReason, UpdateIssueComment

comment = client.send(
    UpdateIssueComment(owner="octo", repo="demo", comment_id=comment.id, body="Fixed in v2.1.")
)
client.send(DeleteIssueComment(owner="octo", repo="demo", comment_id=comment.id))  # None
client.send(
    LockIssue(owner="octo", repo="demo", issue_number=1347, lock_reason=LockReason.RESOLVED)
)  # None; UnlockIssue reverses it
```

Labels and assignees can also be changed *incrementally* — unlike
`UpdateIssue`'s `labels`/`assignees`, which replace the whole set:
{py:class}`~action0.github.operations.labels.AddIssueLabels` /
{py:class}`~action0.github.operations.labels.RemoveIssueLabel` answer
with the resulting label set,
{py:class}`~action0.github.operations.issues.AddAssignees` /
{py:class}`~action0.github.operations.issues.RemoveAssignees` with the
updated issue (the removal is a DELETE carrying a JSON body — GitHub's
design). {py:class}`~action0.github.operations.labels.ListRepoLabels`
and {py:class}`~action0.github.operations.milestones.ListMilestones`
list what a repository has to offer — and an issue carries its
milestone as `issue.milestone`:

```python
from action0.github import AddIssueLabels, ListMilestones, RemoveIssueLabel

labels = client.send(AddIssueLabels(owner="octo", repo="demo", issue_number=1347, labels=["ui"]))
labels = client.send(
    RemoveIssueLabel(owner="octo", repo="demo", issue_number=1347, name="bug")
)  # the remaining set
milestones = client.send(ListMilestones(owner="octo", repo="demo"))
print([m.title for m in milestones], [label.name for label in labels])
```

Both vocabularies are fully manageable too:
{py:class}`~action0.github.operations.labels.CreateLabel` /
{py:class}`~action0.github.operations.labels.UpdateLabel` (renaming
goes through `new_name` and cascades to every issue) /
{py:class}`~action0.github.operations.labels.DeleteLabel`, and
{py:class}`~action0.github.operations.milestones.CreateMilestone` /
{py:class}`~action0.github.operations.milestones.UpdateMilestone` /
{py:class}`~action0.github.operations.milestones.DeleteMilestone`
(deleting a milestone leaves its issues in place, unassigned):

```python
from datetime import datetime, timezone
from action0.github import CreateMilestone, IssueState, UpdateMilestone

milestone = client.send(
    CreateMilestone(
        owner="octo",
        repo="demo",
        title="v1.0",
        due_on=datetime(2026, 10, 9, tzinfo=timezone.utc),
    )
)
milestone = client.send(
    UpdateMilestone(
        owner="octo", repo="demo", milestone_number=milestone.number, state=IssueState.CLOSED
    )
)
```

## Pull requests

{py:class}`~action0.github.operations.pulls.ListPulls` lists a
repository's pull requests, filterable by head and base branch.
{py:class}`~action0.github.operations.pulls.GetPull` fetches one —
including the merge/diff statistics the listings omit (`mergeable`,
`commits`, `additions`, …). A pull request *is* an issue, so `state` is
the same open/closed vocabulary — "merged" is not a state but the
derived `is_merged` (closed with a `merged_at` timestamp):

```python
from action0.github import GetPull, ListPulls, PullStateFilter

pulls = client.send(ListPulls(owner="python", repo="peps", state=PullStateFilter.OPEN))
ready = [p for p in pulls if not p.draft]  # one Page — follow .next for more

pull = client.send(GetPull(owner="python", repo="peps", pull_number=42))
print(pull.is_merged, pull.mergeable, pull.changed_files)  # the stats only GetPull carries
```

{py:class}`~action0.github.operations.pulls.CreatePull` opens one —
`head` is the branch with the changes (`"owner:branch"` for a fork),
`base` the branch to merge into (needs a token with write access):

```python
from action0.github import CreatePull

pull = client.send(
    CreatePull(
        owner="octo",
        repo="demo",
        title="Amazing new feature",
        head="octocat:new-topic",
        base="main",
        draft=True,
    )
)
print(pull.number, pull.html_url)  # the server-assigned number and URL
```

{py:class}`~action0.github.operations.pulls.UpdatePull` edits with the
same PATCH semantics as `UpdateIssue`;
{py:class}`~action0.github.operations.pulls.ListPullFiles` and
{py:class}`~action0.github.operations.pulls.ListPullCommits` page
through the diff and the commits (the same shapes the commit endpoints
use). {py:class}`~action0.github.operations.pulls.MergePull` merges —
pass the `sha` guard and nothing pushed after your last look can slip
in (an unmergeable pull request raises `APIError`, GitHub answers
405/409):

```python
from action0.github import MergeMethod, MergePull

result = client.send(
    MergePull(
        owner="octo",
        repo="demo",
        pull_number=42,
        merge_method=MergeMethod.SQUASH,
        sha=pull.head.sha,  # only merge what was reviewed
    )
)
print(result.merged, result.sha)  # True, the merge commit
```

Reviews:
{py:class}`~action0.github.operations.reviews.ListPullReviews` lists
them, {py:class}`~action0.github.operations.reviews.CreatePullReview`
approves, requests changes or comments (the wire values are uppercase
here — GitHub's one all-caps vocabulary), and
{py:class}`~action0.github.operations.reviews.ListReviewComments`
lists the line-anchored review comments. The conversation thread is
*not* here — that is `ListIssueComments`, because a pull request is an
issue:

```python
from action0.github import CreatePullReview, ListPullReviews, ReviewEvent

reviews = client.send(ListPullReviews(owner="octo", repo="demo", pull_number=42))
review = client.send(
    CreatePullReview(owner="octo", repo="demo", pull_number=42, event=ReviewEvent.APPROVE)
)
print(review.state)  # ReviewState.APPROVED
```

Line comments come in two shapes:
{py:class}`~action0.github.operations.reviews.CreateReviewComment` for
one standalone comment, or a batch of
{py:class}`~action0.github.operations.reviews.DraftReviewComment`
entries submitted *with* a review — one review, one notification,
however many comments (`side` says which half of the diff:
`RIGHT` = the new code):

```python
from action0.github import DraftReviewComment, ReviewSide

review = client.send(
    CreatePullReview(
        owner="octo",
        repo="demo",
        pull_number=42,
        event=ReviewEvent.REQUEST_CHANGES,
        body="Two problems inline.",
        commit_id=pull.head.sha,
        comments=[
            DraftReviewComment(path="src/app.py", body="Off by one.", line=28),
            DraftReviewComment(
                path="src/app.py", body="Reads twice.", line=40, side=ReviewSide.RIGHT
            ),
        ],
    )
)
```

And the review *requests*:
{py:class}`~action0.github.operations.reviews.RequestReviewers` asks
users or teams for a review,
{py:class}`~action0.github.operations.reviews.RemoveRequestedReviewers`
withdraws the ask — both answer with the pull request and its updated
`requested_reviewers`:

```python
from action0.github import RequestReviewers

pull = client.send(
    RequestReviewers(owner="octo", repo="demo", pull_number=42, reviewers=["octocat"])
)
print([user.login for user in pull.requested_reviewers])
```

## Commits

{py:class}`~action0.github.operations.commits.ListCommits` lists a
repository's commits, newest first — filterable by starting ref, author,
time window and touched path (the latter is `file_path` here because
GitHub's parameter name, `path`, is the operation's path template; it is
sent as `path` on the wire). Each commit carries both the git-level
identities (`git_author`/`git_committer` — name, email, date as recorded
in the commit) and the GitHub accounts matched to them (`author`/
`committer` — `None` when the email maps to no account):

```python
from datetime import datetime, timezone
from action0.github import ListCommits

commits = client.send(
    ListCommits(
        owner="python",
        repo="peps",
        file_path="pep-0008.txt",
        since=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
)
for c in commits:  # one Page — follow .next for more
    print(c.sha[:7], c.author.login if c.author else c.git_author.name if c.git_author else "?")
```

{py:class}`~action0.github.operations.commits.GetCommit` fetches one
commit — by sha, branch or tag name — including the diff statistics and
files the listings omit:

```python
from action0.github import GetCommit

commit = client.send(GetCommit(owner="python", repo="peps", ref="main"))
print(commit.additions, commit.deletions)  # only GetCommit carries these
print([(f.status, f.filename) for f in commit.files or []])
```

{py:class}`~action0.github.operations.commits.CompareCommits` compares
two refs — GitHub's three-dot comparison, measuring `head` against the
merge base like `git log base...head`. The endpoint's combined
`{base}...{head}` path segment stays two typed fields here, joined by
the path template:

```python
from action0.github import CompareCommits

diff = client.send(CompareCommits(owner="octo", repo="demo", base="main", head="topic"))
print(diff.status, diff.ahead_by, diff.behind_by)  # e.g. ComparisonStatus.AHEAD 2 0
print([f.filename for f in diff.files])
```

`diff.commits` is capped at 250 (`total_commits` has the real count) and
`diff.files` at 300 — for bigger ranges, list commits page by page via
`ListCommits(sha="topic")`.

## Repository contents

{py:class}`~action0.github.operations.contents.GetContent` fetches a
file or lists a directory. GitHub answers with an *object* for a file
and an *array* for a directory, so the result is the union of the two —
dispatch with `isinstance`:

```python
from action0.github import ContentFile, GetContent

content = client.send(GetContent(owner="octo", repo="demo", file_path="src/app.py"))
if isinstance(content, ContentFile):
    print(content.text)  # bytes arrive base64-encoded; .decoded / .text decode them
else:
    print([entry.path for entry in content])  # a directory listing (no content inlined)
```

The field is `file_path` because GitHub's parameter name, `path`, is
the operation's own path template attribute; `""` lists the repository
root, and `ref` reads from any branch, tag or sha. One size limit to
know: files between 1 and 100 MB arrive with `encoding: "none"` and no
inlined content — `decoded` raises `ValueError` then; fetch the bytes
via the entry's `download_url` instead.

{py:class}`~action0.github.operations.contents.GetReadme` finds the
README whatever it is called (`README.md`, `README.rst`, …):

```python
from action0.github import GetReadme

readme = client.send(GetReadme(owner="python", repo="peps"))
print(readme.name, len(readme.text))
```

Writing goes through the same API — every call is one commit.
{py:class}`~action0.github.operations.contents.CreateOrUpdateFile`
takes *raw bytes*; the base64 transport encoding is applied on
serialization. Create and update are the same endpoint, told apart by
`sha`: `None` creates (422 if the file exists), the file's current blob
sha updates (409 if someone else wrote in between — optimistic locking
for free). {py:class}`~action0.github.operations.contents.DeleteFile`
deletes, also as a commit:

```python
from action0.github import CreateOrUpdateFile, DeleteFile

written = client.send(
    CreateOrUpdateFile(
        owner="octo",
        repo="demo",
        file_path="docs/note.md",
        message="Add a note",
        content=b"# Note\n",  # raw bytes in, base64 on the wire
    )
)
print(written.commit.sha, written.content.sha if written.content else None)

client.send(
    DeleteFile(
        owner="octo",
        repo="demo",
        file_path="docs/note.md",
        message="Remove the note",
        sha=written.content.sha if written.content else "",
    )
)
```

## Branches, tags and repository metadata

{py:class}`~action0.github.operations.branches.ListBranches` /
{py:class}`~action0.github.operations.branches.GetBranch` and
{py:class}`~action0.github.operations.repos.ListRepoTags` cover the
refs; around them, one call each for the contributor list, the
language breakdown and the topics:

```python
from action0.github import GetBranch, ListBranches, ListRepoTags

branches = client.send(ListBranches(owner="python", repo="peps", protected=True))
main = client.send(GetBranch(owner="python", repo="peps", branch="main"))
print([b.name for b in branches], main.sha)  # GetBranch carries the full tip commit

tags = client.send(ListRepoTags(owner="python", repo="cpython", per_page=5))
print([(t.name, t.sha[:7]) for t in tags])
```

```python
from action0.github import GetRepoTopics, ListContributors, ListLanguages, ReplaceRepoTopics

top = client.send(ListContributors(owner="python", repo="peps"))
print([(c.login, c.contributions) for c in top[:3]])
print(client.send(ListLanguages(owner="python", repo="peps")))  # {"Python": 512000, ...}
print(client.send(GetRepoTopics(owner="octo", repo="demo")))
# ReplaceRepoTopics(names=[...]) swaps the whole set — there is no incremental add
```

{py:class}`~action0.github.operations.collaborators.ListCollaborators`
lists who has access (needs push access itself) and
{py:class}`~action0.github.operations.collaborators.GetCollaboratorPermission`
answers with the plain permission string:

```python
from action0.github import CollaboratorAffiliation, GetCollaboratorPermission, ListCollaborators

outside = client.send(
    ListCollaborators(owner="octo", repo="demo", affiliation=CollaboratorAffiliation.OUTSIDE)
)
print(client.send(GetCollaboratorPermission(owner="octo", repo="demo", username="octocat")))
# write
```

## Is this commit green?

Two APIs answer that, and both matter:
{py:class}`~action0.github.operations.statuses.GetCombinedStatus` for
the classic commit statuses (one rolled-up state over all contexts)
and {py:class}`~action0.github.operations.checks.ListCheckRunsForRef`
for the Checks API — GitHub Actions reports *there*, not in the
statuses. The check-runs listing is the one whose payload is not a
bare array; GitHub's `{total_count, check_runs}` envelope is unwrapped
into the usual page:

```python
from action0.github import GetCombinedStatus, ListCheckRunsForRef, StatusState

combined = client.send(GetCombinedStatus(owner="octo", repo="demo", ref=pull.head.sha))
checks = client.send(ListCheckRunsForRef(owner="octo", repo="demo", ref=pull.head.sha))
green = combined.state == StatusState.SUCCESS and all(
    run.conclusion == "success" for run in checks
)
```

## Organizations

{py:class}`~action0.github.operations.orgs.GetOrg` fetches an
organization's profile,
{py:class}`~action0.github.operations.orgs.ListOrgMembers` pages
through its members — the public ones, unless the token belongs to a
member:

```python
from action0.github import GetOrg, ListOrgMembers, OrgMemberRole

org = client.send(GetOrg(org="python"))
admins = client.send(ListOrgMembers(org="python", role=OrgMemberRole.ADMIN))
print(org.name, org.public_repos, [member.login for member in admins])
```

## Releases and asset downloads

{py:class}`~action0.github.operations.releases.ListReleases` lists a
repository's releases (drafts and prereleases included, as far as the
token may see them);
{py:class}`~action0.github.operations.releases.GetLatestRelease`
fetches the most recently published *full* release (drafts and
prereleases never qualify) and
{py:class}`~action0.github.operations.releases.GetReleaseByTag` the
release for a git tag:

```python
from action0.github import GetLatestRelease, GetReleaseByTag, ListReleases

latest = client.send(GetLatestRelease(owner="octo", repo="demo"))
print(latest.tag_name, [a.name for a in latest.assets])
release = client.send(GetReleaseByTag(owner="octo", repo="demo", tag="v1.0.0"))
```

{py:class}`~action0.github.operations.releases.DownloadReleaseAsset`
downloads an asset's binary content — the one operation that is not
JSON: it returns the response body as a
{py:class}`~action0.req.body.BodyProducer`. On a backend opened with
`stream=True` the body is never held in memory; each chunk is written
out as it arrives:

```python
from action0.client.backends.requests import RequestsBackend
from action0.github import DownloadReleaseAsset, GitHubClient

with RequestsBackend(stream=True) as backend:  # a second backend, just for downloads
    download_client = GitHubClient(backend, token="ghp_...")
    asset = latest.assets[0]
    producer = download_client.send(
        DownloadReleaseAsset(owner="octo", repo="demo", asset_id=asset.id)
    )
    with open(asset.name, "wb") as file:
        for chunk in producer.chunks():
            file.write(chunk)
```

On an async backend, iterate `producer.achunks()` with `async for`
instead. Two things to know: GitHub answers the download with a 302
redirect to a short-lived CDN URL, so the backend must follow
redirects (requests, aiohttp and urllib do by default, httpx needs
`follow_redirects=True`) — and keep the `stream=True` backend separate
from the one running JSON operations, whose `load()` reads the whole
body anyway (see the
[action0-client streaming guide](https://laughinjar.github.io/action0-client/usage/streaming.html)).

The write side:
{py:class}`~action0.github.operations.releases.CreateRelease` creates
(a draft, if asked — and can have GitHub generate the notes),
{py:class}`~action0.github.operations.releases.UpdateRelease` edits
with PATCH semantics — publishing a draft is just `draft=False` —
{py:class}`~action0.github.operations.releases.DeleteRelease` deletes
(a `204` no-content operation; the git tag survives), and
{py:class}`~action0.github.operations.releases.GenerateReleaseNotes`
returns the merged-PRs changelog without creating anything, for
editing before publication:

```python
from action0.github import CreateRelease, GenerateReleaseNotes, UpdateRelease

notes = client.send(GenerateReleaseNotes(owner="octo", repo="demo", tag_name="v1.1.0"))
release = client.send(
    CreateRelease(
        owner="octo", repo="demo", tag_name="v1.1.0", name=notes.name, body=notes.body, draft=True
    )
)
release = client.send(UpdateRelease(owner="octo", repo="demo", release_id=release.id, draft=False))
print(release.html_url)
```

{py:class}`~action0.github.operations.releases.UploadReleaseAsset`
attaches a file to a release — **the one operation that does not go to
`api.github.com`**: GitHub takes uploads on a separate host, so send it
through a client pointed at
{py:data}`~action0.github.operations.releases.GITHUB_UPLOADS_URL`
(same token, same backend if you like). The raw bytes are the request
body; a {py:class}`~action0.req.body.FileBody` streams them from disk
instead of holding the file in memory:

```python
from action0.github import GITHUB_UPLOADS_URL, GitHubClient, UploadReleaseAsset
from action0.req import FileBody

upload_client = GitHubClient(backend, token="ghp_...", base_url=GITHUB_UPLOADS_URL)
asset = upload_client.send(
    UploadReleaseAsset(
        owner="octo",
        repo="demo",
        release_id=release.id,
        name="demo-1.1.0.tar.gz",
        content_type="application/gzip",
        data=FileBody("dist/demo-1.1.0.tar.gz"),  # or plain bytes
    )
)
print(asset.id, asset.browser_download_url)
```

## Users

{py:class}`~action0.github.operations.users.GetUser` fetches a public
profile; {py:class}`~action0.github.operations.users.GetAuthenticatedUser`
the one behind the client's token — both as the full
{py:class}`~action0.github.models.user.User` model (a `SimpleUser`
subclass, so it fits wherever an embedded user is expected):

```python
from action0.github import GetAuthenticatedUser, GetUser

user = client.send(GetUser(username="gvanrossum"))
me = client.send(GetAuthenticatedUser())  # requires a token
print(user.name, user.followers, me.login)
```

{py:class}`~action0.github.operations.users.ListFollowers` pages
through a user's followers, and
{py:class}`~action0.github.operations.users.ListUserOrgs` through
their public organization memberships — the entries are
{py:class}`~action0.github.models.org.SimpleOrganization` (the
membership payloads carry no profile fields, not even a web URL), so
follow up with `GetOrg` for the full profile:

```python
from action0.github import ListFollowers, ListUserOrgs

followers = client.send(ListFollowers(username="gvanrossum"))
orgs = client.send(ListUserOrgs(username="gvanrossum"))
print(len(followers), [org.login for org in orgs])
```

## Authentication

Pass a token — classic, fine-grained or app installation — and it is sent
as `Authorization: Bearer` on every request:

```python
client = GitHubClient(backend, token="ghp_...")
```

For GitHub Enterprise Server, point `base_url` at the instance:

```python
client = GitHubClient(backend, token="...", base_url="https://ghe.example.com/api/v3")
```

Every request also carries GitHub's recommended headers by default:
`Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`
and a `User-Agent` (required by GitHub). They are gap-filling defaults —
anything the request sets itself wins.

## Errors

Non-2xx responses raise {py:class}`~action0.client.errors.APIError` (with
`.request` and `.response` attached), transport failures raise
{py:class}`~action0.client.errors.TransportError` — see the
[action0-client error guide](https://laughinjar.github.io/action0-client/usage/errors.html).

## Retries and rate limits

Wrap the backend in action0-client's retrying wrapper (the variant
matching your execution model) and hand it the GitHub-tuned policy:

```python
from action0.client import RetryingSyncBackend
from action0.client.backends.requests import RequestsBackend
from action0.github import GitHubClient, GitHubRetryPolicy

backend = RetryingSyncBackend(RequestsBackend(), GitHubRetryPolicy())
client = GitHubClient(backend, token="ghp_...")
```

{py:class}`~action0.github.retry.GitHubRetryPolicy` keeps the base
behavior (transient 5xx/429, `Retry-After` honored, idempotent methods
only — a `CreateIssue` is never blindly repeated) and adds GitHub's
rate-limit signals: a 403 is retried only when it actually is a rate
limit (`Retry-After` or `x-ratelimit-remaining: 0`), and an exhausted
primary window is waited out until `x-ratelimit-reset` — capped at
`max_backoff` (default 120s; raise it to sit out whole windows). Use
`RetryingAsyncBackend` / `RetryingDeferredBackend` for the other
execution models — the policy is the same.

The proactive complement is
{py:class}`~action0.github.operations.rate_limit.GetRateLimit`: the
current status of every rate limit window, and the call itself does
not count against any limit — check before a burst instead of
reacting to the 403:

```python
from action0.github import GetRateLimit

limits = client.send(GetRateLimit())
print(limits.core.remaining, limits.core.reset)  # e.g. 4999 2026-08-15 13:20:00+00:00
print(limits.search.remaining)  # search has its own, much smaller window
```

## Conditional requests — free revalidation

GitHub answers most GETs with an `ETag`; repeat the request with
`If-None-Match` and an unchanged resource comes back as `304 Not
Modified` — **without counting against the primary rate limit**.
{py:class}`~action0.github.conditional.ConditionalRequestsHook` does
this transparently: it stores ETagged responses, attaches the validators,
and fills a 304 from the store, so your operations only ever see the 200.
It is a hook, not a backend wrapper — one instance drives sync, async and
Twisted backends alike:

```python
from action0.client.backends.requests import RequestsBackend
from action0.github import ConditionalRequestsHook, GitHubClient

backend = RequestsBackend(hooks=[ConditionalRequestsHook()])
client = GitHubClient(backend, token="ghp_...")

repo = client.send(GetRepo(owner="python", repo="cpython"))  # 200, stored
repo = client.send(GetRepo(owner="python", repo="cpython"))  # 304 → served from the store
```

Entries vary on `Accept` and `Authorization` (a different token is a
different entry) and live in an in-memory LRU by default — pass any
{py:class}`~action0.client.caching.CacheStore` to share or persist them.
Combine with {py:class}`~action0.client.caching.CachingSyncBackend` and
hot data skips even the revalidation for the cache's TTL.

## Testing your code

No network needed: the stub backends of
{py:mod}`action0.client.testing` answer with canned responses and record
the requests — exact output shown:

```python
from action0.client.testing import StubBackend
from action0.github import GetRepo, GitHubClient
from action0.req import Response

backend = StubBackend(
    Response(
        200,
        body='{"id": 1, "name": "demo", '
        '"full_name": "octo/demo", "owner": {"login": "octo", "id": 2, '
        '"html_url": "https://github.com/octo", "type": "User"}, "private": false, '
        '"html_url": "https://github.com/octo/demo", "default_branch": "main"}',
    )
)
client = GitHubClient(backend, token="ghp_secret")

print(client.send(GetRepo(owner="octo", repo="demo")).full_name)
# octo/demo
print(backend.requests[0].url.as_str())
# https://api.github.com/repos/octo/demo
```
