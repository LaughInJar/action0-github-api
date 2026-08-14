"""
Conditional requests (:py:class:`ConditionalRequestsHook`): GitHub's
recommended way to save rate limit.

GitHub answers most GETs with an ``ETag`` (and ``Last-Modified``). Repeat
the request with ``If-None-Match`` (/ ``If-Modified-Since``) and, if
nothing changed, GitHub replies ``304 Not Modified`` — with an empty body,
and **without counting against the primary rate limit**. The hook keeps a
store of ETagged responses, attaches the validators on the way out and
fills a 304 from the store on the way in.

Because it is a :py:class:`~action0.client.hooks.Hook` — not a backend
wrapper — a *single* instance drives every execution model: hooks run
inside all backend base classes, sync, async and Twisted alike::

    hook = ConditionalRequestsHook()
    backend = RequestsBackend(hooks=[hook])  # or AsyncHttpxBackend(hooks=[hook]), ...
    client = GitHubClient(backend, token="ghp_...")

Layer :py:class:`~action0.client.caching.CachingSyncBackend` (or its
async/Deferred siblings) around such a backend and hot data is served
without any request for the cache's TTL — after which the request that
does go out is a revalidation, and usually free.
"""

import math

from action0.client import CachePolicy
from action0.client import CacheStore
from action0.client import Hook
from action0.client import MemoryCache
from action0.req import Request
from action0.req import Response

_STASH_KEY = "action0-github:conditional-stored"
"""The ``request.meta`` key carrying the stored response between
:py:meth:`ConditionalRequestsHook.on_request` and
:py:meth:`ConditionalRequestsHook.on_response` — per-request state, so a
shared hook instance stays free of races."""

GITHUB_CONDITIONAL_POLICY = CachePolicy(ttl=math.inf, vary_headers=("Accept", "Authorization"))
"""The default storage policy: entries never expire (an ETag stays valid
until the resource changes; the store's own eviction bounds memory) and
the key varies on ``Accept`` and ``Authorization`` — a different token or
media type is a different cache entry. Keys are sha256 digests, so the
token value never appears in a key."""


class ConditionalRequestsHook(Hook):
    """
    The conditional-requests hook: stores ETagged responses, revalidates
    with ``If-None-Match`` / ``If-Modified-Since``, and turns GitHub's
    ``304 Not Modified`` back into the stored full response — transparently
    to the operations, which only ever see the 200.

    The whole revalidation cycle, against a stub backend:

    >>> from action0.client.testing import StubBackend
    >>> from action0.req import Request, Response
    >>>
    >>> backend = StubBackend(
    ...     Response(200, body='{"name": "cpython"}', headers={"ETag": '"abc"'}),
    ...     Response(304),
    ...     hooks=[ConditionalRequestsHook()],
    ... )
    >>> request = Request("https://api.github.com/repos/python/cpython")
    >>> backend.send(request).body_str()  # stored under its ETag
    '{"name": "cpython"}'
    >>> backend.send(request.copy()).body_str()  # the 304 is filled from the store
    '{"name": "cpython"}'
    >>> backend.requests[1].headers["If-None-Match"]
    '"abc"'
    """

    def __init__(
        self,
        store: CacheStore | None = None,
        policy: CachePolicy = GITHUB_CONDITIONAL_POLICY,
    ) -> None:
        """
        :param store: where the ETagged responses live — any (synchronous)
                      :py:class:`~action0.client.caching.CacheStore`; the
                      default is a fresh, thread-safe
                      :py:class:`~action0.client.caching.MemoryCache`.
                      Hooks run synchronously even on async backends, so
                      an ``AsyncCacheStore`` is not accepted.
        :param policy: what to store under which key —
                       :py:data:`GITHUB_CONDITIONAL_POLICY` unless told
                       otherwise
        """
        self.store = store if store is not None else MemoryCache()
        self.policy = policy

    def on_request(self, request: Request) -> Request | None:
        """
        Attach the stored validators to an outgoing GET/HEAD: the stored
        response's ``ETag`` as ``If-None-Match`` (and ``Last-Modified`` as
        ``If-Modified-Since``). A request already carrying its own
        validators is the caller's conditional request — left untouched.

        :param request: the request about to be sent (mutated in place)
        :return: ``None`` — the given request is the one sent
        """
        if not self.policy.should_lookup(request):
            return None
        if "If-None-Match" in request.headers or "If-Modified-Since" in request.headers:
            return None
        stored = self.store.get(self.policy.key_for(request))
        if stored is None:
            return None
        etag = stored.headers.get("ETag")
        last_modified = stored.headers.get("Last-Modified")
        if etag is None and last_modified is None:
            return None
        if etag is not None:
            request.headers.set("If-None-Match", etag)
        if last_modified is not None:
            request.headers.set("If-Modified-Since", last_modified)
        # carry the matched entry to on_response on the request itself:
        # immune to races on a shared hook and to eviction in between
        request.meta[_STASH_KEY] = stored
        return None

    def on_response(self, request: Request, response: Response, elapsed: float) -> Response | None:
        """
        Fill a ``304 Not Modified`` from the store, and store fresh
        responses that carry validators.

        :param request: the request that was sent
        :param response: the response that arrived
        :param elapsed: the seconds the exchange took (unused)
        :return: the stored full response for a revalidated 304 (an
                 independent copy tied to the current request), else
                 ``None`` to keep the given response
        """
        stored = request.meta.pop(_STASH_KEY, None)
        if response.status == 304 and isinstance(stored, Response):
            # refresh the entry so LRU/TTL recency follows actual use
            self.store.set(self.policy.key_for(request), stored, self.policy.ttl)
            return stored.copy(request=request)
        if self.policy.should_store(request, response) and (
            response.headers.get("ETag") is not None
            or response.headers.get("Last-Modified") is not None
        ):
            self.store.set(self.policy.key_for(request), response.copy(), self.policy.ttl)
        return None
