"""The repository content operations
(`GitHub docs <https://docs.github.com/en/rest/repos/contents>`__)."""

from __future__ import annotations

from typing import Any

from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.content import ContentFile
from ..models.content import DirectoryEntry
from .base import GitHubOperation


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
