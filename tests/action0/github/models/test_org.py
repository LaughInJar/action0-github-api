import unittest

from action0.github import Organization


class OrganizationTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.org.Organization`
    """

    def test_from_json(self) -> None:
        """
        Test that the payload is parsed, with GitHub's ``""`` for a
        cleared ``blog`` normalized to ``None``.
        """
        organization = Organization.from_json(
            {
                "login": "python",
                "id": 1525981,
                "html_url": "https://github.com/python",
                "name": "Python",
                "description": "Repositories related to the Python Programming language",
                "blog": "",
                "location": None,
                "public_repos": 87,
                "followers": 40000,
                "created_at": "2012-03-13T18:19:57Z",
            }
        )

        self.assertEqual(organization.login, "python")
        self.assertEqual(organization.name, "Python")
        self.assertIsNone(organization.blog)  # "" is normalized away
        self.assertEqual(organization.public_repos, 87)
        assert organization.created_at is not None
        self.assertEqual(organization.created_at.year, 2012)
