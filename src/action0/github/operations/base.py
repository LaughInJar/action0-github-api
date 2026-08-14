"""The base class shared by all GitHub operations (:py:class:`GitHubOperation`)."""

from typing import TypeVar

from action0.client import JsonOperation

R_co = TypeVar("R_co", covariant=True)
"""The parsed result type of a GitHub operation."""


class GitHubOperation(JsonOperation[R_co]):
    """
    The base class of all GitHub operations: a
    :py:class:`~action0.client.operation.JsonOperation` requesting GitHub's
    recommended media type.

    ``accept`` lives here (not only as a client default header) because
    :py:meth:`~action0.client.operation.Operation.as_request` sets the
    operation's ``Accept`` before the client's gap-filling defaults run —
    ``JsonOperation``'s plain ``application/json`` would win otherwise.
    """

    accept = "application/vnd.github+json"
