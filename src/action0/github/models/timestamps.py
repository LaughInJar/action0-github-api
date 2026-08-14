"""Parsing GitHub's timestamps, shared by the models."""

from __future__ import annotations

from datetime import datetime


def timestamp(value: str | None) -> datetime | None:
    """
    Parse one of GitHub's ISO 8601 timestamps (``2008-06-11T21:19:53Z``).

    :param value: the timestamp string, or ``None`` where GitHub sends null
    :return: the parsed datetime (timezone-aware), or ``None``
    """
    if value is None:
        return None
    return datetime.fromisoformat(value)
