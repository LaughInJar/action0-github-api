import re
import unittest

import action0.github


class PackageTestCase(unittest.TestCase):
    """
    tests for the :py:mod:`action0.github` package root
    """

    def test_version(self) -> None:
        """
        Test that the version is a non-empty x.y.z string.
        """
        self.assertRegex(action0.github.__version__, re.compile(r"^\d+\.\d+\.\d+$"))

    def test_all_exports_exist(self) -> None:
        """
        Test that everything listed in __all__ is actually importable.
        """
        for name in action0.github.__all__:
            self.assertTrue(hasattr(action0.github, name), f"missing export: {name}")

    def test_dependencies_importable(self) -> None:
        """
        Test that the action0-client, action0-req and action0-url
        dependencies resolve inside the same namespace.
        """
        from action0.client import APIClient
        from action0.req import Request
        from action0.url import Url

        self.assertEqual(Url("https://api.github.com/repos").path, "/repos")
        self.assertEqual(Request("https://api.github.com").method, "GET")
        self.assertTrue(callable(APIClient))
