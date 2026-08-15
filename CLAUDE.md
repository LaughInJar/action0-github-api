# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`action0-github-api` is a fully typed GitHub REST API client built on [`action0-client`](https://github.com/LaughInJar/action0-client): GitHub endpoints are described as typed `Operation` dataclasses and run synchronously, on asyncio or on Twisted — the plugged-in backend decides, and the static types follow it. It serves as the showcase project for the action0 family. It ships the `action0.github` package (`action0` is a PEP 420 namespace package) from a `src/` layout, is built with hatchling, and uses `uv` for environment/dependency management. Runtime dependencies are `action0-client`, `action0-req` and `action0-url` (from PyPI); the HTTP libraries come in through `action0-client`'s optional extras, mirrored here as extras of the same names.

## Rules

- **Never commit without asking.** Also never push, tag, or publish on your own.
- **Branches + PRs.** All changes go through feature branches and GitHub pull requests that Simon reviews and merges — never commit to `main` directly. (Only the initial project scaffold was built directly on `main`; that phase is over.)
- **Discuss first.** Always present the plan and the intended edits and get agreement before changing files.
- Every code change comes with: tests, docstrings, inline comments where the code isn't self-explanatory, and updated usage examples in `README.md` and the Sphinx docs (the guide pages in `docs/usage/`).
- Before considering work done, run ruff, mypy, pyright, ty, and pytest (commands below) and fix what they report.
- Supported Python versions: 3.11 up to the latest release. Don't use syntax or stdlib features introduced after 3.11, and don't rely on behavior removed in newer versions.
- Prefer many small modules and short methods over large files.

## Commands

`uv run` syncs the environment automatically (the dev dependency group, which includes all optional backend libraries, is installed by default), so no separate install step is needed.

```sh
uv run pytest                                        # all tests
uv run pytest tests/action0/github/test_init.py      # one file
uv run pytest tests/action0/github/test_init.py::PackageTestCase::test_version  # one test

uv run ruff check      # lint (add --fix to autofix)
uv run ruff format     # format
uv run mypy            # type-check (strict; files are configured in pyproject.toml)
uv run pyright         # type-check
uv run ty check        # type-check

uv run --group docs sphinx-build -W --keep-going -b html docs docs/_build/html  # build docs

uv build               # build sdist + wheel into dist/
```

`pytest` also runs the `>>>` examples in the docstrings as doctests (`--doctest-modules` over `src/`), so docstring examples must produce their shown output exactly.

## Architecture

The layout under `src/action0/github/` (grows with the implementation; see action0-client's docs for the underlying concepts):

- `__init__.py` — package root, single-sourced `__version__`, re-exports the public API via `__all__`.
- `client.py` — `GitHubClient(APIClient[BackendT_co])`: base URL (overridable for GitHub Enterprise Server), optional bearer token, and GitHub's recommended default headers (`Accept: application/vnd.github+json`, `X-GitHub-Api-Version`, `User-Agent` — required by GitHub) as gap-filling defaults. Imports `__version__` lazily inside `__init__` (the package root imports this module, so a module-level import would be circular).
- `operations/` — one module per GitHub resource area, one operation class per endpoint. `base.py` defines `GitHubOperation(JsonOperation[R_co])`, which pins `accept = "application/vnd.github+json"` — this must live on the operation, not only as a client default, because `as_request` sets the operation's `Accept` before the client's gap-filling defaults run (JsonOperation's plain `application/json` would win otherwise) — plus `PaginatedOperation[ItemT]` (the `per_page`/`page` query fields every listing inherits — base-class fields come first in the query string — returning `Page[ItemT]`: subclasses implement `load_item` per JSON array item; `load` reuses JsonOperation's decode via `super().load` and attaches `next` = `dataclasses.replace(self, page=page+1)` exactly when `links.py` finds `rel="next"` in the response's `Link` header) and the cross-resource `SortDirection` enum. `links.py`: the `Link` header parser (rel → URL; the URL is only used as an existence signal — the next operation is built from the current one, which holds for GitHub's page-number pagination). `repos.py`: `GetRepo`, `ListOrgRepos`/`ListUserRepos` (shared query fields on a private `_ListRepos` base). `issues.py`: `ListIssues` (its `labels` filter is a comma-separated string — GitHub's own wire format, not a repeated param; `since` shows datetime → ISO 8601 query serialization) and `CreateIssue` (JSON body via `json_field()`, `None` fields omitted), `GetIssue`, `UpdateIssue` (first PATCH — every body field optional, `None` = "leave unchanged"; clearing via JSON `null` is not expressible, documented; `state_reason` via `IssueStateReason`) and the comment operations `ListIssueComments`/`CreateIssueComment` (comments are an issues sub-resource — PR conversation comments included). `pulls.py`: `ListPulls` (filters: `PullStateFilter`, `head`/`base` branch, `PullSort` — its `LONG_RUNNING = "long-running"` is the first enum member whose value isn't its lowercased name), `GetPull` (first `int` path param; the full schema carries the merge/diff statistics the listings omit) and `CreatePull`. `releases.py`: `ListReleases`, `GetLatestRelease` ("latest" = newest non-draft non-prerelease, documented), `GetReleaseByTag`, and `DownloadReleaseAsset` — the streaming showcase: subclasses action0-client's plain `Operation[BodyProducer]` (not `GitHubOperation` — `accept` is `application/octet-stream`, not JSON), `load` hands out `response.body_producer() or BytesBody(b"")`; run on a `stream=True` backend, kept separate from the JSON backend; GitHub 302-redirects to its CDN, so the backend must follow redirects (httpx needs `follow_redirects=True`). `users.py`: `GetUser`, `GetAuthenticatedUser` (`GET /user`, needs the token). `search.py`: `SearchOperation` (GitHub wraps search results in a `{total_count, incomplete_results, items}` envelope → `SearchPage`; re-declares the `per_page`/`page` fields because one operation cannot bind both `Page[ItemT]` and `SearchPage[ItemT]` — no higher-kinded types — while the Link-pagination logic is shared via `base.attach_next`) and `SearchRepos` (`q` in GitHub query syntax; search says `order`, not `direction`). Every enumerable request parameter is a `StrEnum` (`RepoSort`, `SortDirection`, `OrgRepoType`, `UserRepoType`, `IssueStateFilter`, `IssueSort`, `IssueStateReason`, `PullStateFilter`, `PullSort`) — client users should get the legal values from IDE completion, not GitHub's docs; keep new operations to that rule.
- `retry.py` — `GitHubRetryPolicy(RetryPolicy)` for action0-client's retrying backend wrappers: retries 403 only when it carries rate-limit signals (`Retry-After` or `x-ratelimit-remaining: 0` — plain permission 403s are not retried), waits until `x-ratelimit-reset` when no `Retry-After` is given (capped at `max_backoff`, default raised to 120s for the ≥60s secondary-limit advice), injectable `clock` for tests. Non-idempotent methods stay non-retried via the base gate.
- `conditional.py` — `ConditionalRequestsHook(Hook)`: GitHub's conditional requests (ETag/`If-None-Match`, `Last-Modified` fallback; 304s don't count against the primary rate limit). Deliberately a *hook*, not a backend wrapper — request mutation + response substitution is exactly what hooks do, so ONE instance drives sync/async/Twisted backends (unlike retry/caching/pagination helpers, which need per-model variants). Reuses action0-client's `CachePolicy` (`GITHUB_CONDITIONAL_POLICY`: ttl `inf`, vary on Accept+Authorization) for keys/storability and `MemoryCache`/`CacheStore` for storage (sync stores only — hooks run synchronously everywhere). The matched entry travels from `on_request` to `on_response` in `request.meta` (race-free on shared hooks, immune to eviction in between). Callers' own `If-None-Match` requests pass through untouched.
- `pagination.py` — the flattening helpers, one per execution model (like action0-client's retry wrappers): `all_items` (sync, lazy generator), `all_items_async` (lazy async generator), `all_items_deferred` (gathers into `Deferred[list[ItemT]]` — a Deferred cannot stream; the Deferred-chaining unwrap is inexpressible in twisted's stubs, hence a documented `cast`). Pagination itself lives in the data (`Page.next`), so manual page loops work in every execution model without these helpers.
- `models/` — plain dataclasses (no validation library, by design — the whole family is dependency-light), one module per model, each with a typed `from_json` classmethod covering the commonly used fields of the GitHub schema (unknown keys ignored, optionals via `.get`). `user.py`: `SimpleUser` and the full profile `User` subclassing it (an embedded user and a profile stay substitutable; GitHub's `""` for a cleared `blog` is normalized to `None`); `repo.py`: `Repo` (`pushed_at` is null on empty repos); `label.py`: `Label` (GitHub sometimes sends labels as bare name strings — `from_json` takes both); `comment.py`: `IssueComment` (issue *and* PR conversation comments — review comments are a separate API); `issue.py`: `Issue` + the `IssueState` enum (GitHub's issue endpoints return pull requests too — `is_pull_request` is derived from the `pull_request` key); `pull.py`: `PullRequest` + the nested `PullRequestRef` (`head`/`base`: branch + sha, `repo`/`user` nullable — deleted forks; `state` reuses `IssueState` — a PR is an issue; "merged" is not a state but the derived `is_merged`, i.e. `merged_at is not None`; the merge/diff statistics are `None` on listing payloads, filled by `GetPull`); `release.py`: `Release` + `ReleaseAsset` (the asset `id` feeds `DownloadReleaseAsset`; `published_at` null on drafts); `timestamps.py`: the shared ISO-8601-to-aware-datetime parsing; `page.py`: `Page[ItemT]`, the Sequence-like listing result carrying `items` + `next` (typed `Operation[Page[ItemT]] | None` — referencing action0-client's `Operation` avoids a models ↔ operations import cycle); `search.py`: `SearchPage(Page)` adding `total_count`/`incomplete_results` (`attach_next` uses `dataclasses.replace`, so Page subclasses survive pagination with their extra fields; note a `SearchPage.next` types as `Operation[Page[ItemT]]` — follow-up pages statically lose the envelope fields, the first page carries them).

`examples/get_repo.py` is the complete worked example (type-checked in CI via mypy's `files`, runnable without network — CI runs it).

Conventions:

- The version is single-sourced as `__version__` in `src/action0/github/__init__.py`; hatch extracts it with the regex in `[tool.hatch.version]`. Bump it only there.
- Releases: pushing a `vX.Y.Z` tag triggers `.github/workflows/release.yml`, which re-runs all checks, verifies the tag matches `__version__`, builds, and publishes to PyPI via trusted publishing (environment `pypi`). Never bump the version, tag, or publish on your own — releasing is the user's call.
- Tests mirror the `src/` layout under `tests/action0/github/` and are `unittest.TestCase` classes, executed via pytest. Network-free: HTTP is faked with `action0.client.testing`'s stub backends; never hit api.github.com in tests.
- Ruff enforces one import per line (isort `force-single-line`), line length 99, `action0` as first-party.
- Docs live in `docs/` (Sphinx + Furo, MyST Markdown pages, autodoc for the API reference). Docstrings are Sphinx-reST (`:param:`, `:py:meth:` roles). CI builds them with `-W` on every run and deploys to GitHub Pages on pushes to `main`. Guide pages go in `docs/usage/` (one page per topic) and show exact outputs in `#` comments — keep them truthful.
