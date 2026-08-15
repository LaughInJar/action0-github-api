import json
import unittest

from action0.client.testing import StubBackend
from action0.github import DownloadReleaseAsset
from action0.github import GetLatestRelease
from action0.github import GetReleaseByTag
from action0.github import GitHubClient
from action0.github import ListReleases
from action0.github import Release
from action0.req import IterableBody
from action0.req import Response

RELEASE_PAYLOAD = {
    "id": 401,
    "tag_name": "v1.0.0",
    "html_url": "https://github.com/octo/demo/releases/tag/v1.0.0",
    "draft": False,
    "prerelease": False,
}


class ListReleasesTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.releases.ListReleases`
    """

    def test_request(self) -> None:
        """
        Test the request shape: only the pagination fields, there are
        no filters.
        """
        request = ListReleases(owner="octo", repo="demo").as_request("https://api.github.com")

        self.assertEqual(request.method, "GET")
        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/releases?per_page=30&page=1",
        )

    def test_parses_into_release_page(self) -> None:
        """
        Test that a JSON array payload is parsed into a
        :py:class:`~action0.github.models.page.Page` of
        :py:class:`Release`.
        """
        backend = StubBackend(Response(200, body=json.dumps([RELEASE_PAYLOAD])))
        client = GitHubClient(backend)

        page = client.send(ListReleases(owner="octo", repo="demo"))

        self.assertEqual([release.tag_name for release in page], ["v1.0.0"])
        self.assertIsInstance(page[0], Release)
        self.assertIsNone(page.next)


class GetLatestReleaseTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.releases.GetLatestRelease`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the request path and that the payload is parsed into a
        :py:class:`Release`.
        """
        backend = StubBackend(Response(200, body=json.dumps(RELEASE_PAYLOAD)))
        client = GitHubClient(backend)

        release = client.send(GetLatestRelease(owner="octo", repo="demo"))

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/releases/latest",
        )
        self.assertIsInstance(release, Release)
        self.assertEqual(release.tag_name, "v1.0.0")


class GetReleaseByTagTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.releases.GetReleaseByTag`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the request path (the tag lands URL-encoded in the path)
        and the parsed :py:class:`Release`.
        """
        backend = StubBackend(Response(200, body=json.dumps(RELEASE_PAYLOAD)))
        client = GitHubClient(backend)

        release = client.send(GetReleaseByTag(owner="octo", repo="demo", tag="v1.0.0"))

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/releases/tags/v1.0.0",
        )
        self.assertEqual(release.tag_name, "v1.0.0")


class DownloadReleaseAssetTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.releases.DownloadReleaseAsset`
    """

    def test_request(self) -> None:
        """
        Test the request shape: the asset id in the path and the
        binary media type — not the JSON one — in ``Accept``.
        """
        request = DownloadReleaseAsset(owner="octo", repo="demo", asset_id=501).as_request(
            "https://api.github.com"
        )

        self.assertEqual(request.method, "GET")
        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/releases/assets/501",
        )
        self.assertEqual(request.headers["Accept"], "application/octet-stream")

    def test_streams_the_body(self) -> None:
        """
        Test that the result is the response's body producer — the
        chunks come out exactly as the (stub) transport delivers them,
        nothing is joined or decoded.
        """
        backend = StubBackend(Response(200, body=IterableBody([b"alpha", b"beta"])))
        client = GitHubClient(backend)

        producer = client.send(DownloadReleaseAsset(owner="octo", repo="demo", asset_id=501))

        self.assertEqual(list(producer.chunks()), [b"alpha", b"beta"])

    def test_empty_body(self) -> None:
        """
        Test that a bodyless response yields an empty producer instead
        of ``None``.
        """
        backend = StubBackend(Response(200))
        client = GitHubClient(backend)

        producer = client.send(DownloadReleaseAsset(owner="octo", repo="demo", asset_id=501))

        self.assertEqual(b"".join(producer.chunks()), b"")
