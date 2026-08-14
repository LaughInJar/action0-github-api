import unittest
from datetime import datetime
from datetime import timezone

from action0.github import Repo
from action0.github import SimpleUser

OWNER_PAYLOAD = {
    "login": "python",
    "id": 1525981,
    "html_url": "https://github.com/python",
    "type": "Organization",
}


class RepoTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.repo.Repo`
    """

    def test_from_json(self) -> None:
        """
        Test that a full repository payload is mapped onto the dataclass.
        """
        repo = Repo.from_json(
            {
                "id": 81598961,
                "name": "cpython",
                "full_name": "python/cpython",
                "owner": OWNER_PAYLOAD,
                "private": False,
                "html_url": "https://github.com/python/cpython",
                "default_branch": "main",
                "description": "The Python programming language",
                "language": "Python",
                "stargazers_count": 60000,
                "forks_count": 29000,
                "open_issues_count": 9000,
                "topics": ["python", "cpython"],
                "archived": False,
                "created_at": "2017-02-10T19:23:51Z",
                "updated_at": "2026-08-14T00:00:00Z",
                "pushed_at": "2026-08-13T21:19:53Z",
                "watchers": 60000,  # unknown keys are ignored
            }
        )

        self.assertEqual(repo.full_name, "python/cpython")
        self.assertEqual(repo.owner, SimpleUser.from_json(OWNER_PAYLOAD))
        self.assertEqual(repo.topics, ["python", "cpython"])
        self.assertEqual(repo.created_at, datetime(2017, 2, 10, 19, 23, 51, tzinfo=timezone.utc))
        self.assertEqual(repo.language, "Python")
        self.assertFalse(repo.archived)

    def test_from_json_minimal(self) -> None:
        """
        Test that a payload with only the required keys maps the optional
        fields to their defaults (GitHub omits ``topics`` unless requested
        and sends ``pushed_at: null`` on empty repositories).
        """
        repo = Repo.from_json(
            {
                "id": 1,
                "name": "empty",
                "full_name": "python/empty",
                "owner": OWNER_PAYLOAD,
                "private": True,
                "html_url": "https://github.com/python/empty",
                "default_branch": "main",
                "description": None,
                "pushed_at": None,
            }
        )

        self.assertIsNone(repo.description)
        self.assertIsNone(repo.language)
        self.assertIsNone(repo.topics)
        self.assertIsNone(repo.created_at)
        self.assertIsNone(repo.pushed_at)
        self.assertEqual(repo.stargazers_count, 0)
        self.assertTrue(repo.private)
