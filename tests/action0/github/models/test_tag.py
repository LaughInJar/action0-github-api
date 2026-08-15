import unittest

from action0.github import Tag


class TagTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.tag.Tag`
    """

    def test_from_json(self) -> None:
        """
        Test that the payload is parsed — the sha comes out of the
        nested ``commit`` pair.
        """
        tag = Tag.from_json(
            {
                "name": "v1.0.0",
                "commit": {"sha": "6dcb09b5", "url": "https://api.github.com/..."},
                "zipball_url": "https://api.github.com/repos/octo/demo/zipball/v1.0.0",
                "tarball_url": "https://api.github.com/repos/octo/demo/tarball/v1.0.0",
            }
        )

        self.assertEqual(tag.name, "v1.0.0")
        self.assertEqual(tag.sha, "6dcb09b5")
        assert tag.zipball_url is not None
        self.assertTrue(tag.zipball_url.endswith("/zipball/v1.0.0"))
