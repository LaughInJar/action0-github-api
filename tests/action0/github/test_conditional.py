import asyncio
import unittest

from action0.client.testing import AsyncStubBackend
from action0.client.testing import DeferredStubBackend
from action0.client.testing import StubBackend
from action0.client.testing import deferred_result
from action0.github import ConditionalRequestsHook
from action0.github import GetRepo
from action0.github import GitHubClient
from action0.req import Request
from action0.req import Response

REPO_BODY = (
    '{"id": 1, "name": "cpython", "full_name": "python/cpython",'
    ' "owner": {"login": "python", "id": 2,'
    ' "html_url": "https://github.com/python", "type": "Organization"},'
    ' "private": false, "html_url": "https://github.com/python/cpython",'
    ' "default_branch": "main"}'
)

ETAGGED = Response(200, body=REPO_BODY, headers={"ETag": '"abc"'})


class ConditionalRequestsHookTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.conditional.ConditionalRequestsHook`
    """

    def test_revalidation_cycle_through_the_client(self) -> None:
        """
        Test the full cycle at the operation level: the first send stores
        the ETagged response, the second carries ``If-None-Match`` and
        parses the 304 as if the stored 200 had arrived.
        """
        backend = StubBackend(ETAGGED, Response(304), hooks=[ConditionalRequestsHook()])
        client = GitHubClient(backend)

        first = client.send(GetRepo(owner="python", repo="cpython"))
        second = client.send(GetRepo(owner="python", repo="cpython"))

        self.assertEqual(first, second)
        self.assertEqual(second.full_name, "python/cpython")
        self.assertNotIn("If-None-Match", backend.requests[0].headers)
        self.assertEqual(backend.requests[1].headers["If-None-Match"], '"abc"')

    def test_vary_headers_separate_the_entries(self) -> None:
        """
        Test that a different Authorization means a different entry: the
        second token's first request goes out unconditional.
        """
        hook = ConditionalRequestsHook()
        backend_a = StubBackend(ETAGGED, hooks=[hook])
        backend_b = StubBackend(ETAGGED, hooks=[hook])

        GitHubClient(backend_a, token="token-one").send(GetRepo(owner="python", repo="cpython"))
        GitHubClient(backend_b, token="token-two").send(GetRepo(owner="python", repo="cpython"))

        self.assertNotIn("If-None-Match", backend_b.requests[0].headers)

    def test_last_modified_fallback(self) -> None:
        """
        Test that a stored response without an ETag revalidates via
        ``If-Modified-Since``.
        """
        dated = Response(
            200, body=REPO_BODY, headers={"Last-Modified": "Wed, 01 Jul 2026 10:00:00 GMT"}
        )
        backend = StubBackend(dated, Response(304), hooks=[ConditionalRequestsHook()])
        client = GitHubClient(backend)

        client.send(GetRepo(owner="python", repo="cpython"))
        repo = client.send(GetRepo(owner="python", repo="cpython"))

        self.assertEqual(repo.full_name, "python/cpython")
        request = backend.requests[1]
        self.assertEqual(request.headers["If-Modified-Since"], "Wed, 01 Jul 2026 10:00:00 GMT")
        self.assertNotIn("If-None-Match", request.headers)

    def test_callers_own_conditional_request_passes_through(self) -> None:
        """
        Test that a request carrying its own ``If-None-Match`` is left
        alone and its 304 is not substituted.
        """
        hook = ConditionalRequestsHook()
        backend = StubBackend(ETAGGED, Response(304), hooks=[hook])
        backend.send(Request("https://api.github.com/repos/python/cpython"))  # fill the store

        request = Request("https://api.github.com/repos/python/cpython")
        request.headers.set("If-None-Match", '"mine"')
        response = backend.send(request)

        self.assertEqual(response.status, 304)
        self.assertEqual(backend.requests[1].headers["If-None-Match"], '"mine"')

    def test_validator_less_responses_are_not_stored(self) -> None:
        """
        Test that a 200 without ETag or Last-Modified is not stored — the
        next request goes out unconditional.
        """
        backend = StubBackend(Response(200, body=REPO_BODY), hooks=[ConditionalRequestsHook()])

        backend.send(Request("https://api.github.com/repos/python/cpython"))
        backend.send(Request("https://api.github.com/repos/python/cpython"))

        self.assertNotIn("If-None-Match", backend.requests[1].headers)

    def test_non_get_responses_are_not_stored(self) -> None:
        """
        Test that non-GET/HEAD exchanges are ignored entirely.
        """
        backend = StubBackend(
            Response(201, body=REPO_BODY, headers={"ETag": '"abc"'}),
            Response(200, body=REPO_BODY, headers={"ETag": '"abc"'}),
            hooks=[ConditionalRequestsHook()],
        )

        backend.send(Request("https://api.github.com/repos/o/r/issues", method="POST"))
        backend.send(Request("https://api.github.com/repos/o/r/issues", method="POST"))

        self.assertNotIn("If-None-Match", backend.requests[1].headers)

    def test_stored_copy_is_independent(self) -> None:
        """
        Test that a revalidated response is an independent copy: mutating
        it does not corrupt later revalidations.
        """
        backend = StubBackend(
            ETAGGED, Response(304), Response(304), hooks=[ConditionalRequestsHook()]
        )

        backend.send(Request("https://api.github.com/repos/python/cpython"))
        revalidated = backend.send(Request("https://api.github.com/repos/python/cpython"))
        revalidated.headers.set("ETag", '"mutated"')

        again = backend.send(Request("https://api.github.com/repos/python/cpython"))
        self.assertEqual(again.headers["ETag"], '"abc"')
        self.assertEqual(backend.requests[2].headers["If-None-Match"], '"abc"')

    def test_same_hook_drives_async_and_deferred_backends(self) -> None:
        """
        Test the execution-model independence: one hook instance, fed by
        a sync backend, revalidates through async and Twisted backends.
        """
        hook = ConditionalRequestsHook()
        StubBackend(ETAGGED, hooks=[hook]).send(
            Request("https://api.github.com/repos/python/cpython")
        )

        async_backend = AsyncStubBackend(Response(304), hooks=[hook])
        response = asyncio.run(
            self._send_async(async_backend, Request("https://api.github.com/repos/python/cpython"))
        )
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body_str(), REPO_BODY)

        deferred_backend = DeferredStubBackend(Response(304), hooks=[hook])
        deferred = deferred_backend.send(Request("https://api.github.com/repos/python/cpython"))
        self.assertEqual(deferred_result(deferred).body_str(), REPO_BODY)

    @staticmethod
    async def _send_async(backend: AsyncStubBackend, request: Request) -> Response:
        """
        :param backend: the async backend to send through
        :param request: the request to send
        :return: the (hook-processed) response
        """
        return await backend.send(request)
