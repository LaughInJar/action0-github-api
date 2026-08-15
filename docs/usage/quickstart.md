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
