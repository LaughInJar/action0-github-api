"""The release operations (`GitHub docs <https://docs.github.com/en/rest/releases>`__)."""

from __future__ import annotations

from typing import Any

from action0.client import Operation
from action0.client import body
from action0.client import header
from action0.client import json_field
from action0.client import path_param
from action0.client import query
from action0.req import BodyProducer
from action0.req import BytesBody
from action0.req import Method
from action0.req import Response

from ..models.release import Release
from ..models.release import ReleaseAsset
from ..models.release import ReleaseNotes
from .base import GitHubOperation
from .base import NoContentOperation
from .base import PaginatedOperation

GITHUB_UPLOADS_URL = "https://uploads.github.com"
"""The base URL of GitHub's upload host — what a client running
:py:class:`UploadReleaseAsset` must be pointed at (uploads do not go to
``api.github.com``)."""


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


class CreateRelease(GitHubOperation[Release]):
    """
    ``POST /repos/{owner}/{repo}/releases`` — create a release (and,
    unless the tag exists already, the tag itself, once the release is
    published). Requires a token with write access.
    """

    method = Method.POST
    path = "/repos/{owner}/{repo}/releases"

    owner: str = path_param()
    repo: str = path_param()

    tag_name: str = json_field()
    """The git tag the release points at — created from
    :py:attr:`target_commitish` if it does not exist yet."""

    target_commitish: str | None = json_field(default=None)
    """The branch or commit to tag if the tag is new; ``None`` uses the
    repository's default branch. Ignored if the tag exists."""

    name: str | None = json_field(default=None)
    """The release title; ``None`` leaves it unset."""

    body: str | None = json_field(default=None)
    """The release notes (GitHub-flavored Markdown)."""

    draft: bool | None = json_field(default=None)
    """Create as an unpublished draft; ``None`` uses GitHub's default
    (``False`` — published immediately)."""

    prerelease: bool | None = json_field(default=None)
    """Mark as a prerelease; ``None`` uses GitHub's default
    (``False``)."""

    generate_release_notes: bool | None = json_field(default=None)
    """Let GitHub generate the notes (appended to :py:attr:`body` if
    both are given); ``None`` uses GitHub's default (``False``). For
    generating without publishing, see
    :py:class:`GenerateReleaseNotes`."""

    def load_json(self, data: Any) -> Release:
        """
        :param data: the decoded JSON payload
        :return: the created release (with its server-assigned id)
        """
        return Release.from_json(data)


class UpdateRelease(GitHubOperation[Release]):
    """
    ``PATCH /repos/{owner}/{repo}/releases/{release_id}`` — update a
    release. PATCH semantics: a ``None`` field is omitted from the body
    and leaves the release untouched (publishing a draft is
    ``draft=False``).
    """

    method = Method.PATCH
    path = "/repos/{owner}/{repo}/releases/{release_id}"

    owner: str = path_param()
    repo: str = path_param()

    release_id: int = path_param()
    """The release id (:py:attr:`Release.id
    <action0.github.models.release.Release.id>` — not the tag)."""

    tag_name: str | None = json_field(default=None)
    """The new tag; ``None`` leaves it unchanged."""

    name: str | None = json_field(default=None)
    """The new title; ``None`` leaves it unchanged."""

    body: str | None = json_field(default=None)
    """The new release notes; ``None`` leaves them unchanged."""

    draft: bool | None = json_field(default=None)
    """Set the draft flag — ``False`` publishes a draft; ``None``
    leaves it unchanged."""

    prerelease: bool | None = json_field(default=None)
    """Set the prerelease flag; ``None`` leaves it unchanged."""

    def load_json(self, data: Any) -> Release:
        """
        :param data: the decoded JSON payload
        :return: the updated release
        """
        return Release.from_json(data)


class DeleteRelease(NoContentOperation):
    """
    ``DELETE /repos/{owner}/{repo}/releases/{release_id}`` — delete a
    release. Answers ``204``. The tag stays — deleting a release does
    not delete the git tag it pointed at.
    """

    method = Method.DELETE
    path = "/repos/{owner}/{repo}/releases/{release_id}"

    owner: str = path_param()
    repo: str = path_param()

    release_id: int = path_param()
    """The release id (not the tag)."""


class GenerateReleaseNotes(GitHubOperation[ReleaseNotes]):
    """
    ``POST /repos/{owner}/{repo}/releases/generate-notes`` — have
    GitHub write release notes (the merged-PRs changelog) for a tag,
    without creating or publishing anything. Feed the result into
    :py:class:`CreateRelease` — or skip this round-trip entirely with
    its ``generate_release_notes`` flag if the text needs no editing.
    """

    method = Method.POST
    path = "/repos/{owner}/{repo}/releases/generate-notes"

    owner: str = path_param()
    repo: str = path_param()

    tag_name: str = json_field()
    """The tag to generate notes for (need not exist yet)."""

    target_commitish: str | None = json_field(default=None)
    """The branch or commit the tag would point at, if it is new;
    ``None`` uses the repository's default branch."""

    previous_tag_name: str | None = json_field(default=None)
    """The tag to diff against; ``None`` lets GitHub pick the previous
    release automatically."""

    def load_json(self, data: Any) -> ReleaseNotes:
        """
        :param data: the decoded JSON payload
        :return: the generated notes
        """
        return ReleaseNotes.from_json(data)


class UploadReleaseAsset(GitHubOperation[ReleaseAsset]):
    """
    ``POST /repos/{owner}/{repo}/releases/{release_id}/assets`` —
    attach a file to a release. **This is the one operation that does
    not go to** ``api.github.com``: GitHub takes uploads on a separate
    host, so send it through a client pointed at
    :py:data:`GITHUB_UPLOADS_URL` (same token; keep it next to your API
    client)::

        upload_client = GitHubClient(backend, token=token, base_url=GITHUB_UPLOADS_URL)
        asset = upload_client.send(UploadReleaseAsset(...))

    The raw bytes are the request body; pass a
    :py:class:`~action0.req.body.FileBody` (or any
    :py:class:`~action0.req.body.BodyProducer`) to stream a large file
    from disk instead of holding it in memory. GitHub answers 422 if an
    asset of that name exists already.
    """

    method = Method.POST
    path = "/repos/{owner}/{repo}/releases/{release_id}/assets"

    owner: str = path_param()
    repo: str = path_param()

    release_id: int = path_param()
    """The release id (not the tag)."""

    name: str = query()
    """The file name the asset gets, e.g. ``"demo-1.0.0.tar.gz"``
    (unusually for a POST, sent as a query parameter — GitHub's
    design, the body being the raw bytes)."""

    data: bytes | BodyProducer = body(repr=False)
    """The file content, raw."""

    content_type: str = header("Content-Type")
    """The asset's MIME type, e.g. ``"application/gzip"`` — becomes
    the ``Content-Type`` of the upload request and later the
    :py:attr:`~action0.github.models.release.ReleaseAsset.content_type`
    served on download."""

    label: str | None = query(default=None)
    """The display label shown instead of the file name; ``None``
    leaves it unset."""

    def load_json(self, data: Any) -> ReleaseAsset:
        """
        :param data: the decoded JSON payload
        :return: the uploaded asset (with its server-assigned id)
        """
        return ReleaseAsset.from_json(data)


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
