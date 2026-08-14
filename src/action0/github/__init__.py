"""
A fully typed GitHub REST API client built on action0-client.

GitHub endpoints are described as typed
:py:class:`~action0.github.operations.base.GitHubOperation` dataclasses
(in :py:mod:`action0.github.operations`, one module per resource area),
their results as plain dataclasses (in :py:mod:`action0.github.models`),
and :py:class:`~action0.github.client.GitHubClient` sends them. Which
execution model runs them — synchronous, asyncio or Twisted — is decided
by the :py:class:`~action0.client.backend.Backend` you plug in, and the
static types follow it.
"""

from .client import GitHubClient
from .models import Repo
from .models import SimpleUser
from .operations import GetRepo
from .operations import GitHubOperation

__version__: str = "0.1.0"

__all__ = [
    "GetRepo",
    "GitHubClient",
    "GitHubOperation",
    "Repo",
    "SimpleUser",
]
