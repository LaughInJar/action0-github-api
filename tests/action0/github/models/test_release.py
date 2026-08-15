import unittest
from datetime import datetime
from datetime import timezone

from action0.github import Release
from action0.github import ReleaseAsset

USER_PAYLOAD = {
    "login": "octocat",
    "id": 1,
    "html_url": "https://github.com/octocat",
    "type": "User",
}

ASSET_PAYLOAD = {
    "id": 501,
    "name": "demo-1.0.0-py3-none-any.whl",
    "content_type": "application/octet-stream",
    "size": 12345,
    "download_count": 42,
    "browser_download_url": (
        "https://github.com/octo/demo/releases/download/v1.0.0/demo-1.0.0-py3-none-any.whl"
    ),
    "label": "wheel",
    "uploader": USER_PAYLOAD,
    "created_at": "2026-08-01T10:00:00Z",
    "updated_at": "2026-08-01T10:05:00Z",
}

RELEASE_PAYLOAD = {
    "id": 401,
    "tag_name": "v1.0.0",
    "html_url": "https://github.com/octo/demo/releases/tag/v1.0.0",
    "draft": False,
    "prerelease": False,
    "name": "Version 1.0.0",
    "body": "First stable release.",
    "author": USER_PAYLOAD,
    "assets": [ASSET_PAYLOAD],
    "target_commitish": "main",
    "created_at": "2026-08-01T09:00:00Z",
    "published_at": "2026-08-01T10:00:00Z",
}


class ReleaseAssetTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.release.ReleaseAsset`
    """

    def test_from_json(self) -> None:
        """
        Test that an asset payload is mapped onto the dataclass.
        """
        asset = ReleaseAsset.from_json(ASSET_PAYLOAD)

        self.assertEqual(asset.id, 501)
        self.assertEqual(asset.name, "demo-1.0.0-py3-none-any.whl")
        self.assertEqual(asset.size, 12345)
        self.assertEqual(asset.download_count, 42)
        self.assertEqual(asset.label, "wheel")
        assert asset.uploader is not None
        self.assertEqual(asset.uploader.login, "octocat")
        self.assertEqual(asset.created_at, datetime(2026, 8, 1, 10, tzinfo=timezone.utc))

    def test_from_json_minimal(self) -> None:
        """
        Test that a payload with only the required keys maps the
        optional fields to their defaults.
        """
        asset = ReleaseAsset.from_json(
            {
                "id": 502,
                "name": "notes.txt",
                "content_type": "text/plain",
                "size": 10,
                "browser_download_url": (
                    "https://github.com/octo/demo/releases/download/v1.0.0/notes.txt"
                ),
            }
        )

        self.assertEqual(asset.download_count, 0)
        self.assertIsNone(asset.label)
        self.assertIsNone(asset.uploader)
        self.assertIsNone(asset.created_at)


class ReleaseTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.release.Release`
    """

    def test_from_json(self) -> None:
        """
        Test that a release payload is mapped onto the dataclass,
        including the nested assets.
        """
        release = Release.from_json(RELEASE_PAYLOAD)

        self.assertEqual(release.tag_name, "v1.0.0")
        self.assertEqual(release.name, "Version 1.0.0")
        self.assertFalse(release.draft)
        self.assertFalse(release.prerelease)
        assert release.author is not None
        self.assertEqual(release.author.login, "octocat")
        self.assertEqual([asset.name for asset in release.assets], ["demo-1.0.0-py3-none-any.whl"])
        self.assertEqual(release.published_at, datetime(2026, 8, 1, 10, tzinfo=timezone.utc))

    def test_from_json_draft(self) -> None:
        """
        Test that a draft's null ``name``/``published_at`` map to
        ``None`` and the optional fields default.
        """
        release = Release.from_json(
            {
                "id": 402,
                "tag_name": "v2.0.0",
                "html_url": "https://github.com/octo/demo/releases/tag/v2.0.0",
                "draft": True,
                "prerelease": False,
                "name": None,
                "published_at": None,
            }
        )

        self.assertTrue(release.draft)
        self.assertIsNone(release.name)
        self.assertIsNone(release.published_at)
        self.assertEqual(release.assets, [])
        self.assertIsNone(release.author)
