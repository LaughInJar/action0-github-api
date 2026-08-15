"""The repository content operations
(`GitHub docs <https://docs.github.com/en/rest/repos/contents>`__)."""

from __future__ import annotations

import base64
from typing import Any

from action0.client import json_field
from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.content import ContentFile
from ..models.content import DirectoryEntry
from ..models.content import FileCommit
from .base import GitHubOperation


def _base64_str(data: bytes) -> str:
    """
    Encode raw file bytes the way the contents API wants them in the
    JSON body.

    :param data: the raw bytes
    :return: the base64 text
    """
    return base64.b64encode(data).decode("ascii")


class GetContent(GitHubOperation[ContentFile | list[DirectoryEntry]]):
    """
    ``GET /repos/{owner}/{repo}/contents/{file_path}`` — fetch a file or
    list a directory.

    GitHub answers with an *object* for a file (base64-encoded content
    inlined) and an *array* for a directory — the result type is the
    union, dispatched on the payload shape:

    >>> operation = GetContent(owner="octo", repo="demo", file_path="src/app.py")
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/octo/demo/contents/src/app.py'

    (The field is ``file_path`` because ``path`` is the operation's own
    path template attribute; an empty string lists the repository
    root.)
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/contents/{file_path}"

    owner: str = path_param()
    repo: str = path_param()

    file_path: str = path_param()
    """The path within the repository — a file for a
    :py:class:`~action0.github.models.content.ContentFile` result, a
    directory (or ``""`` for the root) for a list of
    :py:class:`~action0.github.models.content.DirectoryEntry`."""

    ref: str | None = query(default=None)
    """The branch, tag or sha to read from; ``None`` uses the
    repository's default branch."""

    def load_json(self, data: Any) -> ContentFile | list[DirectoryEntry]:
        """
        :param data: the decoded JSON payload — object or array
        :return: the file, or the directory listing
        """
        if isinstance(data, list):
            return [DirectoryEntry.from_json(item) for item in data]
        return ContentFile.from_json(data)


class GetReadme(GitHubOperation[ContentFile]):
    """
    ``GET /repos/{owner}/{repo}/readme`` — fetch a repository's README,
    whatever it is called (``README.md``, ``README.rst``, …).

    >>> operation = GetReadme(owner="python", repo="peps")
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/python/peps/readme'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/readme"

    owner: str = path_param()
    repo: str = path_param()

    ref: str | None = query(default=None)
    """The branch, tag or sha to read from; ``None`` uses the
    repository's default branch."""

    def load_json(self, data: Any) -> ContentFile:
        """
        :param data: the decoded JSON payload
        :return: the README file
        """
        return ContentFile.from_json(data)


class CreateOrUpdateFile(GitHubOperation[FileCommit]):
    """
    ``PUT /repos/{owner}/{repo}/contents/{file_path}`` — create a file,
    or update one (requires a token with write access; every call is
    one commit).

    Create and update are the same endpoint, told apart by :py:attr:`sha`:
    ``None`` creates — GitHub answers 422 if the file already exists —
    and passing the file's current blob sha updates, answering 409 on a
    mismatch (someone else wrote in between; both surface as
    :py:class:`~action0.client.errors.APIError`). Pass raw bytes as
    :py:attr:`content` — the base64 transport encoding is applied on
    serialization (a ``serialize=`` field hook).
    """

    method = Method.PUT
    path = "/repos/{owner}/{repo}/contents/{file_path}"

    owner: str = path_param()
    repo: str = path_param()

    file_path: str = path_param()
    """The path of the file within the repository."""

    message: str = json_field()
    """The commit message."""

    content: bytes = json_field(serialize=_base64_str, repr=False)
    """The new file content, raw — base64 happens on the wire."""

    sha: str | None = json_field(default=None)
    """The blob sha the file currently has
    (:py:attr:`~action0.github.models.content.ContentFile.sha`) when
    updating; ``None`` creates a new file."""

    branch: str | None = json_field(default=None)
    """The branch to commit to; ``None`` uses the repository's default
    branch."""

    def load_json(self, data: Any) -> FileCommit:
        """
        :param data: the decoded JSON payload
        :return: the created commit and the written file (whose fresh
                 ``sha`` the next update of the same file needs)
        """
        return FileCommit.from_json(data)


class DeleteFile(GitHubOperation[FileCommit]):
    """
    ``DELETE /repos/{owner}/{repo}/contents/{file_path}`` — delete a
    file, as one commit. Unusually for a DELETE it carries a JSON body
    (the commit message and the blob sha) *and* answers with one — the
    commit — so this is no
    :py:class:`~action0.github.operations.base.NoContentOperation`.
    """

    method = Method.DELETE
    path = "/repos/{owner}/{repo}/contents/{file_path}"

    owner: str = path_param()
    repo: str = path_param()

    file_path: str = path_param()
    """The path of the file within the repository."""

    message: str = json_field()
    """The commit message."""

    sha: str = json_field()
    """The blob sha the file currently has — required; GitHub answers
    409 on a mismatch."""

    branch: str | None = json_field(default=None)
    """The branch to commit to; ``None`` uses the repository's default
    branch."""

    def load_json(self, data: Any) -> FileCommit:
        """
        :param data: the decoded JSON payload
        :return: the deleting commit (``content`` is ``None``)
        """
        return FileCommit.from_json(data)
