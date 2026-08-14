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

repos = client.send(  # a list[Repo]
    ListOrgRepos(org="python", sort=RepoSort.PUSHED, direction=SortDirection.DESC, per_page=10)
)
```

Pagination is manual for now — pass `page=2` etc. (a paginator that
follows the `Link` header is on the roadmap).

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
