"""The client (:py:class:`GitHubClient`): base URL, default headers and auth."""

from __future__ import annotations

from action0.client import APIClient
from action0.client import BackendT_co


class GitHubClient(APIClient[BackendT_co]):
    """
    The GitHub REST API client: base URL, GitHub's recommended headers and
    (optional) token auth baked in. Which execution model runs it is the
    backend's choice — see :py:class:`~action0.client.api.APIClient`.

    Example (with the test-double backend standing in for a real one)::

        >>> from action0.client.testing import StubBackend
        >>> from action0.req import Response
        >>>
        >>> backend = StubBackend(Response(200, body="{}"))
        >>> client = GitHubClient(backend, token="ghp_secret")
        >>> client
        GitHubClient(https://api.github.com via StubBackend(0 requests))
    """

    def __init__(
        self,
        backend: BackendT_co,
        token: str | None = None,
        base_url: str = "https://api.github.com",
    ) -> None:
        """
        :param backend: any sync, async or Twisted backend
        :param token: a GitHub token (classic, fine-grained or app
                      installation) sent as ``Authorization: Bearer``;
                      ``None`` sends unauthenticated requests (public data
                      only, 60 requests/hour)
        :param base_url: the API root — override for GitHub Enterprise
                         Server (``https://HOST/api/v3``)
        """
        # the package root imports this module, so __version__ can only be
        # imported once the package is fully initialized — i.e. at call time
        from action0.github import __version__

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            # GitHub rejects requests without a User-Agent
            "User-Agent": f"action0-github-api/{__version__}",
        }
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        super().__init__(backend, base_url, headers=headers)
