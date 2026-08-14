"""
The result models — plain dataclasses the operations hand to the
application, each with a ``from_json`` classmethod building it from the
decoded API payload. They cover the commonly used fields of the GitHub
schemas, not every last one.
"""

from .repo import Repo
from .user import SimpleUser

__all__ = [
    "Repo",
    "SimpleUser",
]
