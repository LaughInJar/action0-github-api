"""The collaborator operations
(`GitHub docs <https://docs.github.com/en/rest/collaborators/collaborators>`__)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.user import SimpleUser
from .base import GitHubOperation
from .base import PaginatedOperation


class CollaboratorAffiliation(StrEnum):
    """The affiliation filter of :py:class:`ListCollaborators`."""

    OUTSIDE = "outside"
    DIRECT = "direct"
    ALL = "all"


class ListCollaborators(PaginatedOperation[SimpleUser]):
    """
    ``GET /repos/{owner}/{repo}/collaborators`` — list who has access
    to a repository (requires a token with push access itself).

    >>> operation = ListCollaborators(
    ...     owner="octo", repo="demo", affiliation=CollaboratorAffiliation.DIRECT
    ... )
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/repos/octo/demo/collaborators?per_page=30&page=1&affiliation=direct'
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/collaborators"

    owner: str = path_param()
    repo: str = path_param()

    affiliation: CollaboratorAffiliation | None = query(default=None)
    """Filter by how the access came about — outside collaborators,
    direct ones, or everyone; ``None`` uses GitHub's default
    (``all``)."""

    permission: str | None = query(default=None)
    """Only collaborators with (at least) this permission — one of
    GitHub's role names (``"pull"``, ``"triage"``, ``"push"``,
    ``"maintain"``, ``"admin"`` or a custom role — an open set, hence
    no enum); ``None`` lists all."""

    def load_item(self, data: Any) -> SimpleUser:
        """
        :param data: one decoded JSON array item
        :return: the collaborator
        """
        return SimpleUser.from_json(data)


class GetCollaboratorPermission(GitHubOperation[str]):
    """
    ``GET /repos/{owner}/{repo}/collaborators/{username}/permission`` —
    what one user may do in a repository. The answer is reduced to the
    permission string itself: ``"admin"``, ``"write"``, ``"read"`` or
    ``"none"``.
    """

    method = Method.GET
    path = "/repos/{owner}/{repo}/collaborators/{username}/permission"

    owner: str = path_param()
    repo: str = path_param()

    username: str = path_param()
    """The login to look up."""

    def load_json(self, data: Any) -> str:
        """
        :param data: the decoded JSON payload
        :return: the permission level
        """
        return str(data["permission"])
