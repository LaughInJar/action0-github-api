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
