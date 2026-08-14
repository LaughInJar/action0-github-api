"""
A fully typed GitHub REST API client built on action0-client.

GitHub endpoints are described as typed :py:class:`action0.client.Operation`
dataclasses; which execution model runs them — synchronous, asyncio or
Twisted — is decided by the :py:class:`action0.client.Backend` you plug in,
and the static types follow it.
"""

__version__: str = "0.1.0"

__all__: list[str] = []
