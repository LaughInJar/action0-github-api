"""The release operations (`GitHub docs <https://docs.github.com/en/rest/releases>`__)."""

from __future__ import annotations

from typing import Any

from action0.client import Operation
from action0.client import path_param
from action0.req import BodyProducer
from action0.req import BytesBody
from action0.req import Method
from action0.req import Response

from ..models.release import Release
from .base import GitHubOperation
from .base import PaginatedOperation


class ListReleases(PaginatedOperation[Release]):
    """
    ``GET /repos/{owner}/{repo}/releases`` — list a repository's
    releases, most recent first (drafts and prereleases included, as
    far as the token may see them).

    >>> operation = ListReleases(owner="python", repo="cpython", per_page=5)
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/cpython/releases?per_page=5&page=1'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/releases"

    owner: str = path_param()
    repo: str = path_param()

    def load_item(self, data: Any) -> Release:
        """
        :param data: one decoded JSON array item
        :return: the release
        """
        return Release.from_json(data)


class GetLatestRelease(GitHubOperation[Release]):
    """
    ``GET /repos/{owner}/{repo}/releases/latest`` — fetch the latest
    release. "Latest" is the most recently published *full* release:
    drafts and prereleases never qualify, so this can be older than the
    first entry of :py:class:`ListReleases`.
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/releases/latest"

    owner: str = path_param()
    repo: str = path_param()

    def load_json(self, data: Any) -> Release:
        """
        :param data: the decoded JSON payload
        :return: the release
        """
        return Release.from_json(data)


class GetReleaseByTag(GitHubOperation[Release]):
    """
    ``GET /repos/{owner}/{repo}/releases/tags/{tag}`` — fetch the
    release for a git tag.

    >>> operation = GetReleaseByTag(owner="octo", repo="demo", tag="v1.0.0")
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/octo/demo/releases/tags/v1.0.0'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/releases/tags/{tag}"

    owner: str = path_param()
    repo: str = path_param()
    tag: str = path_param()

    def load_json(self, data: Any) -> Release:
        """
        :param data: the decoded JSON payload
        :return: the release
        """
        return Release.from_json(data)


class DownloadReleaseAsset(Operation[BodyProducer]):
    """
    ``GET /repos/{owner}/{repo}/releases/assets/{asset_id}`` with
    ``Accept: application/octet-stream`` — download an asset's binary
    content.

    Unlike every other operation this is not a
    :py:class:`~action0.github.operations.base.GitHubOperation`: the
    result is not JSON but the raw body, handed out as a
    :py:class:`~action0.req.body.BodyProducer`. Run it on a backend
    with ``stream=True`` and the body is never held in memory — iterate
    :py:meth:`~action0.req.body.BodyProducer.chunks` (sync) or
    :py:meth:`~action0.req.body.BodyProducer.achunks` (async) and write
    the chunks out as they arrive. Keep that streaming backend separate
    from the one running JSON operations (backends are cheap to have
    two of).

    Two GitHub particulars:

    - GitHub answers with a **302 redirect** to a short-lived CDN URL,
      so the backend must follow redirects — requests, aiohttp and
      urllib do by default, httpx needs ``follow_redirects=True``.
    - The asset id comes from
      :py:attr:`~action0.github.models.release.ReleaseAsset.id`, not
      from the browser download URL.
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/releases/assets/{asset_id}"
    accept = "application/octet-stream"

    owner: str = path_param()
    repo: str = path_param()
    asset_id: int = path_param()

    def load(self, response: Response) -> BodyProducer:
        """
        Hand out the response body as a producer — nothing reads it
        until the caller iterates.

        :param response: the response, already vetted
        :return: the body producer (an empty producer for a bodyless
                 response)
        """
        return response.body_producer() or BytesBody(b"")
