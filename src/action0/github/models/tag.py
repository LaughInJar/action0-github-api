"""The tag model (:py:class:`Tag`)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Tag:
    """
    A repository tag, as
    :py:class:`~action0.github.operations.repos.ListRepoTags` returns
    it: a name pinned to a commit, plus GitHub's on-the-fly source
    archives.
    """

    name: str
    """The tag name, e.g. ``"v1.0.0"``."""

    sha: str
    """The sha of the tagged commit."""

    zipball_url: str | None = None
    """The URL of the generated ``.zip`` source archive."""

    tarball_url: str | None = None
    """The URL of the generated ``.tar.gz`` source archive."""

    @classmethod
    def from_json(cls, data: Any) -> Tag:
        """
        Build a tag from one decoded JSON object.

        :param data: the decoded JSON object
        :return: the tag
        """
        return cls(
            name=data["name"],
            sha=data["commit"]["sha"],
            zipball_url=data.get("zipball_url"),
            tarball_url=data.get("tarball_url"),
        )
