"""The organization operations
(`GitHub docs <https://docs.github.com/en/rest/orgs/orgs>`__)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from action0.client import path_param
from action0.client import query
from action0.req import Method

from ..models.org import Organization
from ..models.user import SimpleUser
from .base import GitHubOperation
from .base import PaginatedOperation


class OrgMemberRole(StrEnum):
    """The role filter of :py:class:`ListOrgMembers`."""

    ALL = "all"
    ADMIN = "admin"
    MEMBER = "member"


class GetOrg(GitHubOperation[Organization]):
    """
    ``GET /orgs/{org}`` — fetch an organization's public profile (plus
    the private counters, if the token is a member's).

    >>> operation = GetOrg(org="python")
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/orgs/python'
    """

    method = Method.GET
    path = "/orgs/{org}"

    org: str = path_param()

    def load_json(self, data: Any) -> Organization:
        """
        :param data: the decoded JSON payload
        :return: the organization
        """
        return Organization.from_json(data)


class ListOrgMembers(PaginatedOperation[SimpleUser]):
    """
    ``GET /orgs/{org}/members`` — list an organization's members
    (only the public ones, unless the token is a member's).

    >>> operation = ListOrgMembers(org="python", role=OrgMemberRole.ADMIN)
    >>> operation.as_request("https://api.github.com").url.as_str()
    'https://api.github.com/orgs/python/members?per_page=30&page=1&role=admin'
    """

    method = Method.GET
    path = "/orgs/{org}/members"

    org: str = path_param()

    role: OrgMemberRole | None = query(default=None)
    """The role filter; ``None`` uses GitHub's default (``all``)."""

    def load_item(self, data: Any) -> SimpleUser:
        """
        :param data: one decoded JSON array item
        :return: the member
        """
        return SimpleUser.from_json(data)
