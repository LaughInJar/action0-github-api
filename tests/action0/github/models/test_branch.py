import unittest

from action0.github import Branch


class BranchTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.branch.Branch`
    """

    def test_from_json_listing(self) -> None:
        """
        Test a listing payload: ``commit`` is a bare ``{sha, url}``
        pair, so the full commit stays ``None``.
        """
        branch = Branch.from_json(
            {
                "name": "main",
                "commit": {"sha": "6dcb09b5", "url": "https://api.github.com/..."},
                "protected": True,
            }
        )

        self.assertEqual(branch.name, "main")
        self.assertEqual(branch.sha, "6dcb09b5")
        self.assertTrue(branch.protected)
        self.assertIsNone(branch.commit)

    def test_from_json_detail(self) -> None:
        """
        Test a GetBranch payload: ``commit`` is a full commit object
        (recognized by its nested ``commit`` key) and gets parsed.
        """
        branch = Branch.from_json(
            {
                "name": "main",
                "commit": {
                    "sha": "6dcb09b5",
                    "html_url": "https://github.com/octo/demo/commit/6dcb09b5",
                    "commit": {"message": "Fix all the bugs"},
                    "parents": [],
                },
                "protected": False,
            }
        )

        assert branch.commit is not None
        self.assertEqual(branch.commit.message, "Fix all the bugs")
        self.assertEqual(branch.sha, "6dcb09b5")
