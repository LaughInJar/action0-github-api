# action0-github-api

A fully typed [GitHub REST API](https://docs.github.com/en/rest) client
built on [action0-client](https://laughinjar.github.io/action0-client/):
GitHub endpoints are described once, as typed operation dataclasses, and
run synchronously, on asyncio or on Twisted — decided by the backend you
plug in. The type checker follows along: the same `send()` returns a
value, an `Awaitable` or a `Deferred`, depending on the backend.

```shell
uv add "action0-github-api[httpx]"
```

```python
client = GitHubClient(RequestsBackend())
repo = client.send(GetRepo(owner="python", repo="cpython"))  # Repo

client = GitHubClient(AsyncHttpxBackend())
repo = await client.send(GetRepo(owner="python", repo="cpython"))  # Awaitable[Repo]

client = GitHubClient(TwistedBackend())
deferred = client.send(GetRepo(owner="python", repo="cpython"))  # Deferred[Repo]
```

```{note}
This project is under construction — the first operations are in place
and the endpoint coverage grows from here.
```

```{toctree}
:maxdepth: 2

usage/index
api
```
