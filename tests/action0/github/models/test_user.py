import unittest

from action0.github import SimpleUser


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
