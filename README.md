# Action0-GitHub-API

[![CI](https://github.com/LaughInJar/action0-github-api/actions/workflows/ci.yml/badge.svg)](https://github.com/LaughInJar/action0-github-api/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/action0-github-api)](https://pypi.org/project/action0-github-api/)

A fully typed [GitHub REST API](https://docs.github.com/en/rest) client
built on [action0-client](https://github.com/LaughInJar/action0-client):
GitHub endpoints are described once, as typed operation dataclasses, and
run synchronously, on asyncio or on Twisted — decided by the backend you
plug in. The type checker follows along: the same `send()` returns a
value, an `Awaitable` or a `Deferred`, depending on the backend.

```python
client = GitHubClient(RequestsBackend())
repo = client.send(GetRepo(owner="python", repo="cpython"))  # Repo

client = GitHubClient(AsyncHttpxBackend())
repo = await client.send(GetRepo(owner="python", repo="cpython"))  # Awaitable[Repo]

client = GitHubClient(TwistedBackend())
deferred = client.send(GetRepo(owner="python", repo="cpython"))  # Deferred[Repo]
```

## Installation

Pick the extra matching the HTTP backend you want to run on (the stdlib
`urllib` and thread-pool backends of action0-client need no extra):

```shell
uv add "action0-github-api[httpx]"     # or [requests], [aiohttp], [urllib3], [twisted], [all]
```

## Usage

```python
from action0.client.backends.requests import RequestsBackend
from action0.github import CreateIssue, DownloadReleaseAsset, GetLatestRelease, GetRepo
from action0.github import GetUser, GitHubClient, IssueState, IssueStateReason, ListOrgRepos
from action0.github import ListPulls, PullStateFilter, RepoSearchSort, RepoSort
from action0.github import SearchRepos, UpdateIssue, all_items

with RequestsBackend() as backend:
    client = GitHubClient(backend)  # token="ghp_..." for higher rate limits
    repo = client.send(GetRepo(owner="python", repo="cpython"))
    print(repo.full_name, repo.language, repo.stargazers_count)

    repos = client.send(ListOrgRepos(org="python", sort=RepoSort.PUSHED, per_page=10))
    print([r.name for r in repos])  # one Page[Repo]; repos.next is the next page's operation

    for repo in all_items(client, ListOrgRepos(org="python")):  # or follow all pages lazily
        print(repo.full_name)

    pulls = client.send(ListPulls(owner="python", repo="peps", state=PullStateFilter.OPEN))
    print([p.title for p in pulls if not p.draft])  # p.head/p.base name the branches

    user = client.send(GetUser(username="gvanrossum"))
    print(user.name, user.followers)

    hits = client.send(SearchRepos(q="http client language:python", sort=RepoSearchSort.STARS))
    print(hits.total_count, [r.full_name for r in hits])
```

Writing works the same way — the typed fields become the JSON body
(needs a token). Updates are PATCH semantics: `None` fields are
omitted and stay untouched:

```python
issue = client.send(CreateIssue(owner="octo", repo="demo", title="Found a bug", labels=["bug"]))
issue = client.send(
    UpdateIssue(
        owner="octo",
        repo="demo",
        issue_number=issue.number,
        state=IssueState.CLOSED,
        state_reason=IssueStateReason.COMPLETED,
    )
)
```

Release assets download as a stream — on a `stream=True` backend the
body is never held in memory (GitHub 302-redirects to its CDN, so the
backend must follow redirects; most do by default):

```python
with RequestsBackend(stream=True) as backend:  # a second backend, just for downloads
    release = client.send(GetLatestRelease(owner="octo", repo="demo"))
    asset = release.assets[0]
    producer = GitHubClient(backend).send(
        DownloadReleaseAsset(owner="octo", repo="demo", asset_id=asset.id)
    )
    with open(asset.name, "wb") as file:
        for chunk in producer.chunks():
            file.write(chunk)
```

Rate limits are handled by wrapping the backend with action0-client's
retrying wrapper and the GitHub-tuned policy — and saved in the first
place by the conditional-requests hook, which revalidates via `ETag`
(GitHub's 304 answers don't count against the rate limit):

```python
backend = RetryingSyncBackend(
    RequestsBackend(hooks=[ConditionalRequestsHook()]),
    GitHubRetryPolicy(),
)
client = GitHubClient(backend, token="ghp_...")
```

See the [quickstart](https://laughinjar.github.io/action0-github-api/usage/quickstart.html)
for asyncio/Twisted usage, authentication, GitHub Enterprise Server and
testing without network — and `examples/get_repo.py` for a complete,
runnable example.

## Status

Under construction — the first operations are in place and the endpoint
coverage grows from here. Documentation:
<https://laughinjar.github.io/action0-github-api/>

## License

MIT — see [LICENSE](LICENSE).
