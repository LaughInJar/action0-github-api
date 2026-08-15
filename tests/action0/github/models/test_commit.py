import unittest
from datetime import datetime
from datetime import timezone

from action0.github import Commit
from action0.github import CommitFile
from action0.github import CommitFileStatus
from action0.github import GitIdentity
from action0.github import SimpleUser

LISTING_PAYLOAD = {
    "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
    "html_url": "https://github.com/octo/demo/commit/6dcb09b5b57875f334f61aebed695e2e4193db5e",
    "commit": {
        "message": "Fix all the bugs",
        "author": {
            "name": "Monalisa Octocat",
            "email": "mona@github.com",
            "date": "2026-08-14T10:00:00Z",
        },
        "committer": {
            "name": "GitHub",
            "email": "noreply@github.com",
            "date": "2026-08-14T10:00:01Z",
        },
    },
    "author": {
        "login": "octocat",
        "id": 1,
        "html_url": "https://github.com/octocat",
        "type": "User",
    },
    "committer": None,
    "parents": [{"sha": "553c2077f0edc3d5dc5d17262f6aa498e69d6f8e"}],
}


class CommitTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.commit.Commit`
    """

    def test_from_json_listing(self) -> None:
        """
        Test a listing payload: message and git identities flattened out
        of the nested ``commit`` object, the account-level ``committer``
        null, no diff statistics.
        """
        commit = Commit.from_json(LISTING_PAYLOAD)

        self.assertEqual(commit.sha, "6dcb09b5b57875f334f61aebed695e2e4193db5e")
        self.assertEqual(commit.message, "Fix all the bugs")
        assert commit.git_author is not None
        self.assertIsInstance(commit.git_author, GitIdentity)
        self.assertEqual(commit.git_author.email, "mona@github.com")
        self.assertEqual(
            commit.git_author.date, datetime(2026, 8, 14, 10, 0, 0, tzinfo=timezone.utc)
        )
        assert commit.author is not None
        self.assertIsInstance(commit.author, SimpleUser)
        self.assertEqual(commit.author.login, "octocat")
        self.assertIsNone(commit.committer)  # no GitHub account matched
        self.assertEqual(commit.parents, ["553c2077f0edc3d5dc5d17262f6aa498e69d6f8e"])
        # the diff statistics are None until GetCommit fills them
        self.assertIsNone(commit.additions)
        self.assertIsNone(commit.deletions)
        self.assertIsNone(commit.files)

    def test_from_json_detail(self) -> None:
        """
        Test a detail (GetCommit) payload: ``stats`` flattened to
        ``additions``/``deletions``, the ``files`` parsed.
        """
        payload = dict(
            LISTING_PAYLOAD,
            stats={"additions": 10, "deletions": 3, "total": 13},
            files=[
                {
                    "filename": "src/new_name.py",
                    "status": "renamed",
                    "additions": 10,
                    "deletions": 3,
                    "changes": 13,
                    "patch": "@@ -1 +1 @@",
                    "previous_filename": "src/old_name.py",
                }
            ],
        )

        commit = Commit.from_json(payload)

        self.assertEqual(commit.additions, 10)
        self.assertEqual(commit.deletions, 3)
        assert commit.files is not None
        (file,) = commit.files
        self.assertIsInstance(file, CommitFile)
        self.assertEqual(file.status, CommitFileStatus.RENAMED)
        self.assertEqual(file.previous_filename, "src/old_name.py")
        self.assertEqual(file.patch, "@@ -1 +1 @@")

    def test_from_json_unmatched_author(self) -> None:
        """
        Test that a null account-level ``author`` (email not mapped to
        any GitHub account) stays ``None`` while the git identity is
        still there.
        """
        commit = Commit.from_json(dict(LISTING_PAYLOAD, author=None))

        self.assertIsNone(commit.author)
        assert commit.git_author is not None
        self.assertEqual(commit.git_author.name, "Monalisa Octocat")


class CommitFileTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.commit.CommitFile`
    """

    def test_from_json_binary_file(self) -> None:
        """
        Test that a binary file's missing ``patch`` stays ``None``.
        """
        file = CommitFile.from_json(
            {
                "filename": "logo.png",
                "status": "added",
                "additions": 0,
                "deletions": 0,
                "changes": 0,
            }
        )

        self.assertEqual(file.status, CommitFileStatus.ADDED)
        self.assertIsNone(file.patch)
        self.assertIsNone(file.previous_filename)
