import unittest
from datetime import datetime
from datetime import timezone

from action0.github import SimpleUser
from action0.github import User


class SimpleUserTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.user.SimpleUser`
    """

    def test_from_json(self) -> None:
        """
        Test that a user payload is mapped onto the dataclass.
        """
        user = SimpleUser.from_json(
            {
                "login": "python",
                "id": 1525981,
                "html_url": "https://github.com/python",
                "type": "Organization",
                "node_id": "MDEyOk9yZ2FuaXphdGlvbjE1MjU5ODE=",  # unknown keys are ignored
            }
        )

        self.assertEqual(
            user,
            SimpleUser(
                login="python",
                id=1525981,
                html_url="https://github.com/python",
                type="Organization",
            ),
        )


class UserTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.user.User`
    """

    def test_from_json(self) -> None:
        """
        Test that a full profile payload is mapped onto the dataclass —
        including the SimpleUser core it extends.
        """
        user = User.from_json(
            {
                "login": "gvanrossum",
                "id": 2894642,
                "html_url": "https://github.com/gvanrossum",
                "type": "User",
                "name": "Guido van Rossum",
                "company": None,
                "blog": "",  # GitHub sends "" for a cleared blog field
                "location": "San Francisco Bay Area",
                "email": None,
                "bio": "Python's BDFL-emeritus",
                "public_repos": 30,
                "public_gists": 4,
                "followers": 20000,
                "following": 5,
                "created_at": "2012-11-25T16:53:03Z",
                "updated_at": "2026-08-01T00:00:00Z",
            }
        )

        self.assertEqual(user.login, "gvanrossum")
        self.assertEqual(user.name, "Guido van Rossum")
        self.assertIsNone(user.blog)
        self.assertEqual(user.location, "San Francisco Bay Area")
        self.assertEqual(user.followers, 20000)
        self.assertEqual(user.created_at, datetime(2012, 11, 25, 16, 53, 3, tzinfo=timezone.utc))
        # a full profile still is a SimpleUser wherever one is expected
        self.assertIsInstance(user, SimpleUser)

    def test_from_json_minimal(self) -> None:
        """
        Test that a payload with only the SimpleUser core maps the
        profile fields to their defaults.
        """
        user = User.from_json(
            {
                "login": "octocat",
                "id": 1,
                "html_url": "https://github.com/octocat",
                "type": "User",
            }
        )

        self.assertIsNone(user.name)
        self.assertIsNone(user.bio)
        self.assertEqual(user.public_repos, 0)
        self.assertIsNone(user.created_at)
