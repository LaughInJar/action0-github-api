"""
Fetching a repository from the GitHub API, in every execution model:
the same :py:class:`~action0.github.operations.repos.GetRepo` operation
and :py:class:`~action0.github.client.GitHubClient`, driven synchronously,
with asyncio, and with Twisted — only the backend changes.

Run it (no network involved, the demo uses the stub backend)::

    uv run python examples/get_repo.py
"""

from __future__ import annotations

from action0.github import ConditionalRequestsHook
from action0.github import CreateIssue
from action0.github import GetRepo
from action0.github import GetUser
from action0.github import GitHubClient
from action0.github import GitHubRetryPolicy
from action0.github import ListOrgRepos
from action0.github import Repo
from action0.github import RepoSearchSort
from action0.github import RepoSort
from action0.github import SearchRepos
from action0.github import all_items


def sync_usage() -> None:
    """The client with the (sync) requests backend."""
    from action0.client.backends.requests import RequestsBackend

    with RequestsBackend() as backend:
        client = GitHubClient(backend)  # token=... for higher rate limits
        repo: Repo = client.send(GetRepo(owner="python", repo="cpython"))
        print(repo.full_name, repo.stargazers_count)


async def async_usage() -> None:
    """The same operation with the async httpx backend."""
    from action0.client.backends.httpx import AsyncHttpxBackend

    async with AsyncHttpxBackend() as backend:
        client = GitHubClient(backend)
        repo: Repo = await client.send(GetRepo(owner="python", repo="cpython"))
        print(repo.full_name, repo.stargazers_count)


def twisted_usage() -> None:
    """The same operation on Twisted, as a Deferred."""
    from typing import Any
    from typing import cast

    from twisted.internet import reactor as _reactor
    from twisted.internet.defer import Deferred

    from action0.client.backends.twisted import TwistedBackend

    # the global reactor is a zope-interface object type checkers can't
    # follow — treat it as Any, like most typed twisted code does
    reactor = cast(Any, _reactor)

    client = GitHubClient(TwistedBackend())
    deferred: Deferred[Repo] = client.send(GetRepo(owner="python", repo="cpython"))
    deferred.addCallback(lambda repo: print(repo.full_name))
    deferred.addBoth(lambda _: reactor.stop())
    reactor.run()


# ---------------------------------------------------------------------------
# A runnable, network-free demo: the stub backend answers instead of
# api.github.com — which is also exactly how an application would test
# its code.


def demo() -> None:
    """Exercise the client against a canned response and print the result."""
    from action0.client.testing import StubBackend
    from action0.req import Response

    payload = """{
        "id": 81598961, "name": "cpython", "full_name": "python/cpython",
        "owner": {"login": "python", "id": 1525981,
                  "html_url": "https://github.com/python", "type": "Organization"},
        "private": false, "html_url": "https://github.com/python/cpython",
        "default_branch": "main", "language": "Python", "stargazers_count": 60000
    }"""
    issue_payload = """{
        "id": 101, "number": 1347, "title": "Found a bug", "state": "open",
        "html_url": "https://github.com/python/cpython/issues/1347", "user": null
    }"""
    # a Link header on the first listing page announces the second one
    next_link = '<https://api.github.com/orgs/python/repos?page=2>; rel="next"'
    user_payload = """{
        "login": "gvanrossum", "id": 2894642, "type": "User",
        "html_url": "https://github.com/gvanrossum",
        "name": "Guido van Rossum", "followers": 20000
    }"""
    backend = StubBackend(
        Response(200, body=payload),
        Response(200, body=f"[{payload}]", headers={"Link": next_link}),
        Response(200, body="[]"),
        Response(201, body=issue_payload),
        Response(200, body=user_payload),
        Response(200, body=f'{{"total_count": 1234, "items": [{payload}]}}'),
    )
    client = GitHubClient(backend, token="ghp_secret")

    repo = client.send(GetRepo(owner="python", repo="cpython"))
    print(repo.full_name, "-", repo.language, "-", repo.stargazers_count, "stars")

    # the listings take enum filters — IDE completion knows the legal
    # values — and all_items follows the Link header across the pages
    repos = all_items(client, ListOrgRepos(org="python", sort=RepoSort.PUSHED, per_page=10))
    print("repos of python:", [r.name for r in repos])

    # writes work the same: the typed fields become the JSON body
    issue = client.send(
        CreateIssue(owner="python", repo="cpython", title="Found a bug", labels=["bug"])
    )
    print("created issue:", issue.number, issue.state)

    user = client.send(GetUser(username="gvanrossum"))
    print("user:", user.name, "-", user.followers, "followers")

    # search results come in an envelope: a SearchPage with total_count
    hits = client.send(SearchRepos(q="language:python", sort=RepoSearchSort.STARS))
    print("search:", hits.total_count, "matches, first page:", [r.name for r in hits])

    print("requests sent:")
    for request in backend.requests:
        print("  ", request.method, request.url.as_str())

    # rate limits: the GitHub-tuned policy waits out a rate-limited 403
    # (fake clock and sleep here) and retries — the second attempt wins
    from action0.client import RetryingSyncBackend

    rate_limited = Response(
        403,
        body='{"message": "API rate limit exceeded"}',
        headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "30"},
    )
    retrying = RetryingSyncBackend(
        StubBackend(rate_limited, Response(200, body=payload)),
        GitHubRetryPolicy(clock=lambda: 0.0),
        sleep=lambda seconds: print(f"rate limited - waiting {seconds:.0f}s (pretend)"),
    )
    retrying_client = GitHubClient(retrying, token="ghp_secret")
    print("after retry:", retrying_client.send(GetRepo(owner="python", repo="cpython")).full_name)

    # conditional requests: the second fetch revalidates with If-None-Match
    # and GitHub's 304 answer (free, rate-limit-wise) is filled from the store
    conditional = StubBackend(
        Response(200, body=payload, headers={"ETag": '"abc"'}),
        Response(304),
        hooks=[ConditionalRequestsHook()],
    )
    conditional_client = GitHubClient(conditional)
    print("fetched:", conditional_client.send(GetRepo(owner="python", repo="cpython")).language)
    print(
        "revalidated:", conditional_client.send(GetRepo(owner="python", repo="cpython")).language
    )
    print("second request sent If-None-Match:", conditional.requests[1].headers["If-None-Match"])


if __name__ == "__main__":
    demo()
