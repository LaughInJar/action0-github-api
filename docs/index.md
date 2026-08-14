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

```{note}
This project is under construction — the first operations are being
built. The pages below grow with the implementation.
```

```{toctree}
:maxdepth: 2

api
```
