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
- `operations/` — one module per GitHub resource area, one operation class per endpoint. `base.py` defines `GitHubOperation(JsonOperation[R_co])`, which pins `accept = "application/vnd.github+json"` — this must live on the operation, not only as a client default, because `as_request` sets the operation's `Accept` before the client's gap-filling defaults run (JsonOperation's plain `application/json` would win otherwise). `repos.py`: `GetRepo`, `ListOrgRepos`/`ListUserRepos` (shared query fields on a private `_ListRepos` base; pagination is manual via `page=` until a Link-header paginator exists). Every enumerable request parameter is a `StrEnum` (`RepoSort`, `SortDirection`, `OrgRepoType`, `UserRepoType`) — client users should get the legal values from IDE completion, not GitHub's docs; keep new operations to that rule.
- `models/` — plain dataclasses (no validation library, by design — the whole family is dependency-light), one module per model, each with a typed `from_json` classmethod covering the commonly used fields of the GitHub schema (unknown keys ignored, optionals via `.get`). `user.py`: `SimpleUser`; `repo.py`: `Repo` (ISO 8601 timestamps parsed to aware datetimes; `pushed_at` is null on empty repos).

`examples/get_repo.py` is the complete worked example (type-checked in CI via mypy's `files`, runnable without network — CI runs it).

Conventions:

- The version is single-sourced as `__version__` in `src/action0/github/__init__.py`; hatch extracts it with the regex in `[tool.hatch.version]`. Bump it only there.
- Releases: pushing a `vX.Y.Z` tag triggers `.github/workflows/release.yml`, which re-runs all checks, verifies the tag matches `__version__`, builds, and publishes to PyPI via trusted publishing (environment `pypi`). Never bump the version, tag, or publish on your own — releasing is the user's call.
- Tests mirror the `src/` layout under `tests/action0/github/` and are `unittest.TestCase` classes, executed via pytest. Network-free: HTTP is faked with `action0.client.testing`'s stub backends; never hit api.github.com in tests.
- Ruff enforces one import per line (isort `force-single-line`), line length 99, `action0` as first-party.
- Docs live in `docs/` (Sphinx + Furo, MyST Markdown pages, autodoc for the API reference). Docstrings are Sphinx-reST (`:param:`, `:py:meth:` roles). CI builds them with `-W` on every run and deploys to GitHub Pages on pushes to `main`. Guide pages go in `docs/usage/` (one page per topic) and show exact outputs in `#` comments — keep them truthful.
