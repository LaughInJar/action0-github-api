import json
import unittest

from action0.client.testing import StubBackend
from action0.github import GITHUB_UPLOADS_URL
from action0.github import CreateRelease
from action0.github import DeleteRelease
from action0.github import DownloadReleaseAsset
from action0.github import GenerateReleaseNotes
from action0.github import GetLatestRelease
from action0.github import GetReleaseByTag
from action0.github import GitHubClient
from action0.github import ListReleases
from action0.github import Release
from action0.github import ReleaseAsset
from action0.github import ReleaseNotes
from action0.github import UpdateRelease
from action0.github import UploadReleaseAsset
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


class CreateReleaseTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.releases.CreateRelease`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the POST body (``None`` fields omitted) and the parsing of
        the created release.
        """
        backend = StubBackend(Response(201, body=json.dumps(RELEASE_PAYLOAD)))
        client = GitHubClient(backend, token="ghp_secret")

        release = client.send(
            CreateRelease(
                owner="octo",
                repo="demo",
                tag_name="v1.0.0",
                name="Version 1.0.0",
                generate_release_notes=True,
            )
        )

        request = backend.requests[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.url.as_str(), "https://api.github.com/repos/octo/demo/releases")
        body = request.body_str()
        assert body is not None
        self.assertEqual(
            json.loads(body),
            {"tag_name": "v1.0.0", "name": "Version 1.0.0", "generate_release_notes": True},
        )
        self.assertIsInstance(release, Release)
        self.assertEqual(release.id, 401)


class UpdateReleaseTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.releases.UpdateRelease`
    """

    def test_request_publishes_draft(self) -> None:
        """
        Test the PATCH shape for the common move: publishing a draft is
        just ``draft=False``, everything else stays untouched.
        """
        request = UpdateRelease(owner="octo", repo="demo", release_id=401, draft=False).as_request(
            "https://api.github.com"
        )

        self.assertEqual(request.method, "PATCH")
        self.assertEqual(
            request.url.as_str(), "https://api.github.com/repos/octo/demo/releases/401"
        )
        body = request.body_str()
        assert body is not None
        self.assertEqual(json.loads(body), {"draft": False})


class DeleteReleaseTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.releases.DeleteRelease`
    """

    def test_request_and_none_result(self) -> None:
        """
        Test the no-content round trip: DELETE out, ``204`` in, ``None``
        back.
        """
        backend = StubBackend(Response(204))
        client = GitHubClient(backend, token="ghp_secret")

        result = client.send(DeleteRelease(owner="octo", repo="demo", release_id=401))

        self.assertEqual(backend.requests[0].method, "DELETE")
        self.assertIsNone(result)


class GenerateReleaseNotesTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.releases.GenerateReleaseNotes`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the POST request and the :py:class:`ReleaseNotes` parsing.
        """
        payload = {"name": "v1.1.0", "body": "## What's Changed\n* Fix all the bugs"}
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend, token="ghp_secret")

        notes = client.send(
            GenerateReleaseNotes(
                owner="octo", repo="demo", tag_name="v1.1.0", previous_tag_name="v1.0.0"
            )
        )

        request = backend.requests[0]
        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/releases/generate-notes",
        )
        body = request.body_str()
        assert body is not None
        self.assertEqual(json.loads(body), {"tag_name": "v1.1.0", "previous_tag_name": "v1.0.0"})
        self.assertIsInstance(notes, ReleaseNotes)
        self.assertEqual(notes.name, "v1.1.0")


class UploadReleaseAssetTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.releases.UploadReleaseAsset`
    """

    def test_request_against_uploads_host(self) -> None:
        """
        Test the full upload shape on the uploads host: the file name in
        the query, the raw bytes as the body, the declared content type.
        """
        asset_payload = {
            "id": 501,
            "name": "demo-1.0.0.tar.gz",
            "content_type": "application/gzip",
            "size": 9,
            "download_count": 0,
            "browser_download_url": "https://github.com/octo/demo/releases/download/v1.0.0/demo-1.0.0.tar.gz",
        }
        backend = StubBackend(Response(201, body=json.dumps(asset_payload)))
        client = GitHubClient(backend, token="ghp_secret", base_url=GITHUB_UPLOADS_URL)

        asset = client.send(
            UploadReleaseAsset(
                owner="octo",
                repo="demo",
                release_id=401,
                name="demo-1.0.0.tar.gz",
                content_type="application/gzip",
                data=b"tar bytes",
            )
        )

        request = backend.requests[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(
            request.url.as_str(),
            "https://uploads.github.com/repos/octo/demo/releases/401/assets"
            "?name=demo-1.0.0.tar.gz",
        )
        self.assertEqual(request.headers["Content-Type"], "application/gzip")
        self.assertEqual(request.body, b"tar bytes")
        self.assertIsInstance(asset, ReleaseAsset)
        self.assertEqual(asset.id, 501)
