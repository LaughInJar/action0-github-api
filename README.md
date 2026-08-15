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
from action0.github import CompareCommits, CreateIssue, CreateOrUpdateFile
from action0.github import DownloadReleaseAsset, GetCombinedStatus, GetLatestRelease
from action0.github import GetRateLimit, GetReadme, GetRepo, GetUser, GitHubClient, IssueState
from action0.github import IssueStateReason, ListCommits, ListOrgRepos, ListPulls, MergeMethod
from action0.github import MergePull, PullStateFilter, RepoSearchSort, RepoSort, SearchRepos
from action0.github import UpdateIssue, all_items

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

    commits = client.send(ListCommits(owner="python", repo="peps", file_path="pep-0008.txt"))
    print([c.message.splitlines()[0] for c in commits])  # newest first

    diff = client.send(CompareCommits(owner="python", repo="peps", base="main", head="topic"))
    print(diff.status, diff.ahead_by, [f.filename for f in diff.files])

    readme = client.send(GetReadme(owner="python", repo="peps"))
    print(readme.text[:40])  # contents arrive base64-encoded — .text decodes

    user = client.send(GetUser(username="gvanrossum"))
    print(user.name, user.followers)

    hits = client.send(SearchRepos(q="http client language:python", sort=RepoSearchSort.STARS))
    print(hits.total_count, [r.full_name for r in hits])

    limits = client.send(GetRateLimit())  # this call doesn't count against any limit
    print(limits.core.remaining, limits.search.remaining)
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

status = client.send(GetCombinedStatus(owner="octo", repo="demo", ref="main"))
result = client.send(  # merge once the statuses and checks are green
    MergePull(owner="octo", repo="demo", pull_number=42, merge_method=MergeMethod.SQUASH)
)

written = client.send(  # committing a file is one call — raw bytes in, base64 on the wire
    CreateOrUpdateFile(
        owner="octo", repo="demo", file_path="docs/note.md", message="Add note", content=b"# Hi\n"
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

Uploading works too — `UploadReleaseAsset` streams a file to a release,
sent through a client pointed at `GITHUB_UPLOADS_URL` (GitHub takes
uploads on a separate host).

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

The core resource areas are covered: repositories (contents incl.
file writes, branches, tags, topics, languages, contributors,
collaborators), issues (comments, labels, milestones, assignees —
each fully manageable), pull requests (merging, reviews incl. line
comments, review requests), commits (incl. statuses and check runs),
releases (CRUD, generated notes, streaming asset down- and uploads),
users, organizations, search and rate limits.
Documentation: <https://laughinjar.github.io/action0-github-api/>

## AI disclosure

This library is developed with heavy use of AI coding tools: the code,
tests, and documentation are largely written by
[Claude Code](https://claude.com/claude-code), working from the author's
design brief and reviewed by the author. If that changes how much you want
to rely on this package, that's a fair call — read the source, it's small.

## License

MIT — see [LICENSE](LICENSE).
