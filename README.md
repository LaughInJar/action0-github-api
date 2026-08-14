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

## Status

Under construction — the project scaffold is in place, the first
operations are being built. Documentation:
<https://laughinjar.github.io/action0-github-api/>

## License

MIT — see [LICENSE](LICENSE).
