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
from action0.github import GetRepo, GitHubClient

with RequestsBackend() as backend:
    client = GitHubClient(backend)  # token="ghp_..." for higher rate limits
    repo = client.send(GetRepo(owner="python", repo="cpython"))
    print(repo.full_name, repo.language, repo.stargazers_count)
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
