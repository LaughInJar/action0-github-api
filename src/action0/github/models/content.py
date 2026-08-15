"""The repository content models (:py:class:`ContentFile`,
:py:class:`DirectoryEntry`, :py:class:`FileCommit`)."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .commit import GitCommit


class ContentType(StrEnum):
    """What a repository content entry is."""

    FILE = "file"
    DIR = "dir"
    SYMLINK = "symlink"
    SUBMODULE = "submodule"


@dataclass
class ContentFile:
    """
    A file fetched through the contents API — the object payload of
    :py:class:`~action0.github.operations.contents.GetContent` and
    :py:class:`~action0.github.operations.contents.GetReadme`.

    The bytes arrive base64-encoded in :py:attr:`content`; use
    :py:attr:`decoded` (or :py:attr:`text`) instead of touching the raw
    transport encoding.
    """

    name: str
    """The file name, e.g. ``"README.md"``."""

    path: str
    """The path within the repository."""

    sha: str
    """The git blob sha (what update/delete operations would need)."""

    size: int
    """The file size in bytes."""

    type: ContentType
    """What the entry is — requesting a symlink or submodule path
    yields an object without content."""

    html_url: str | None = None
    """The web URL."""

    download_url: str | None = None
    """The direct (CDN) download URL — the fallback for files whose
    content GitHub does not inline."""

    encoding: str | None = None
    """The transport encoding of :py:attr:`content` — ``"base64"``, or
    ``"none"`` when GitHub declined to inline the bytes (files between
    1 and 100 MB; fetch those via :py:attr:`download_url`)."""

    content: str | None = None
    """The base64-encoded bytes (use :py:attr:`decoded`)."""

    @property
    def decoded(self) -> bytes:
        """
        The decoded file bytes.

        :raises ValueError: if the payload carries no inlined content
                (``encoding: "none"``, or a symlink/submodule entry) —
                fetch via :py:attr:`download_url` instead
        """
        if self.content is None or self.encoding != "base64":
            raise ValueError(
                f"{self.path}: no inlined content (encoding={self.encoding!r})"
                " — fetch via download_url"
            )
        return base64.b64decode(self.content)

    @property
    def text(self) -> str:
        """
        The decoded file content as text (UTF-8).

        :raises ValueError: if the payload carries no inlined content
        :raises UnicodeDecodeError: if the bytes are not valid UTF-8
        """
        return self.decoded.decode("utf-8")

    @classmethod
    def from_json(cls, data: Any) -> ContentFile:
        """
        Build a content file from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the content file
        """
        return cls(
            name=data["name"],
            path=data["path"],
            sha=data["sha"],
            size=data["size"],
            type=ContentType(data["type"]),
            html_url=data.get("html_url"),
            download_url=data.get("download_url"),
            encoding=data.get("encoding"),
            content=data.get("content"),
        )


@dataclass
class DirectoryEntry:
    """
    One entry of a directory listing — the array items
    :py:class:`~action0.github.operations.contents.GetContent` returns
    for a directory path. Entries carry no content; fetch a file of
    interest with its own ``GetContent(file_path=entry.path)``.
    """

    name: str
    """The entry name, e.g. ``"app.py"``."""

    path: str
    """The path within the repository."""

    sha: str
    """The git object sha."""

    size: int
    """The file size in bytes (0 for directories)."""

    type: ContentType
    """What the entry is."""

    html_url: str | None = None
    """The web URL."""

    download_url: str | None = None
    """The direct download URL (``None`` for directories)."""

    @classmethod
    def from_json(cls, data: Any) -> DirectoryEntry:
        """
        Build a directory entry from one decoded JSON array item.

        :param data: the decoded JSON array item
        :return: the entry
        """
        return cls(
            name=data["name"],
            path=data["path"],
            sha=data["sha"],
            size=data["size"],
            type=ContentType(data["type"]),
            html_url=data.get("html_url"),
            download_url=data.get("download_url"),
        )


@dataclass
class FileCommit:
    """
    The answer of the contents *write* operations
    (:py:class:`~action0.github.operations.contents.CreateOrUpdateFile`,
    :py:class:`~action0.github.operations.contents.DeleteFile`): the
    commit GitHub created, plus the resulting file entry.
    """

    commit: GitCommit
    """The commit the write produced."""

    content: ContentFile | None = None
    """The written file — its fresh blob :py:attr:`~ContentFile.sha` is
    what the *next* update of the same file needs. ``None`` after a
    delete."""

    @classmethod
    def from_json(cls, data: Any) -> FileCommit:
        """
        Build a file commit from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the file commit
        """
        content = data.get("content")
        return cls(
            commit=GitCommit.from_json(data["commit"]),
            content=ContentFile.from_json(content) if content is not None else None,
        )
