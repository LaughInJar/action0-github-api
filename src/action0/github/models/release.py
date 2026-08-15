"""The release models (:py:class:`Release`, :py:class:`ReleaseAsset`,
:py:class:`ReleaseNotes`)."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any

from .timestamps import timestamp
from .user import SimpleUser


@dataclass
class ReleaseAsset:
    """
    A file attached to a release.

    This is GitHub's ``release-asset`` schema, reduced to the commonly
    used fields. The :py:attr:`id` is what
    :py:class:`~action0.github.operations.releases.DownloadReleaseAsset`
    takes; :py:attr:`browser_download_url` is the browser-facing link
    (no API authentication — public repositories only).
    """

    id: int
    """The numeric asset id (globally unique)."""

    name: str
    """The file name, e.g. ``"demo-1.0.0-py3-none-any.whl"``."""

    content_type: str
    """The MIME type the asset was uploaded as."""

    size: int
    """The file size in bytes."""

    download_count: int
    """How often the asset was downloaded."""

    browser_download_url: str
    """The browser-facing download URL."""

    label: str | None = None
    """The display label, if one was set."""

    uploader: SimpleUser | None = None
    """Who uploaded the asset (``None`` e.g. for deleted accounts)."""

    created_at: datetime | None = None
    """When the asset was uploaded."""

    updated_at: datetime | None = None
    """When the asset was last changed."""

    @classmethod
    def from_json(cls, data: Any) -> ReleaseAsset:
        """
        Build an asset from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the asset
        """
        uploader = data.get("uploader")
        return cls(
            id=data["id"],
            name=data["name"],
            content_type=data["content_type"],
            size=data["size"],
            download_count=data.get("download_count", 0),
            browser_download_url=data["browser_download_url"],
            label=data.get("label"),
            uploader=SimpleUser.from_json(uploader) if uploader is not None else None,
            created_at=timestamp(data.get("created_at")),
            updated_at=timestamp(data.get("updated_at")),
        )


@dataclass
class ReleaseNotes:
    """
    Auto-generated release notes — what
    :py:class:`~action0.github.operations.releases.GenerateReleaseNotes`
    returns. Nothing is published; feed the text into
    :py:class:`~action0.github.operations.releases.CreateRelease` (or
    let it generate the notes itself via ``generate_release_notes``).
    """

    name: str
    """The suggested release title."""

    body: str
    """The generated notes (GitHub-flavored Markdown)."""

    @classmethod
    def from_json(cls, data: Any) -> ReleaseNotes:
        """
        Build release notes from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the release notes
        """
        return cls(name=data["name"], body=data["body"])


@dataclass
class Release:
    """
    A GitHub release.

    This is GitHub's ``release`` schema, reduced to the commonly used
    fields.
    """

    id: int
    """The numeric release id (globally unique)."""

    tag_name: str
    """The git tag the release points at, e.g. ``"v1.0.0"``."""

    html_url: str
    """The web URL, e.g.
    ``"https://github.com/octo/demo/releases/tag/v1.0.0"``."""

    draft: bool
    """Whether the release is an unpublished draft."""

    prerelease: bool
    """Whether the release is marked as a prerelease."""

    name: str | None = None
    """The release title, if one was set."""

    body: str | None = None
    """The release notes (GitHub-flavored Markdown), if any."""

    author: SimpleUser | None = None
    """Who created the release (``None`` e.g. for deleted accounts)."""

    assets: list[ReleaseAsset] = field(default_factory=list)
    """The attached files (source archives are not assets — GitHub
    generates those on the fly)."""

    target_commitish: str | None = None
    """The branch or commit the tag was created from."""

    created_at: datetime | None = None
    """When the commit the release points at was created."""

    published_at: datetime | None = None
    """When the release was published (``None`` on drafts)."""

    @classmethod
    def from_json(cls, data: Any) -> Release:
        """
        Build a release from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the release
        """
        author = data.get("author")
        return cls(
            id=data["id"],
            tag_name=data["tag_name"],
            html_url=data["html_url"],
            draft=data["draft"],
            prerelease=data["prerelease"],
            name=data.get("name"),
            body=data.get("body"),
            author=SimpleUser.from_json(author) if author is not None else None,
            assets=[ReleaseAsset.from_json(item) for item in data.get("assets", [])],
            target_commitish=data.get("target_commitish"),
            created_at=timestamp(data.get("created_at")),
            published_at=timestamp(data.get("published_at")),
        )
