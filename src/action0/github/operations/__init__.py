"""
The GitHub endpoints as typed operation classes — one module per GitHub
resource area, one :py:class:`~action0.github.operations.base.GitHubOperation`
subclass per endpoint.
"""

from .base import GitHubOperation
from .repos import GetRepo

__all__ = [
    "GetRepo",
    "GitHubOperation",
]
