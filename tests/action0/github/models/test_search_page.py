import unittest

from action0.github import Page
from action0.github import SearchPage


class SearchPageTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.search.SearchPage`
    """

    def test_is_a_page_with_envelope_fields(self) -> None:
        """
        Test that a search page keeps the sequence behavior and adds the
        envelope fields.
        """
        page = SearchPage(items=["a", "b"], total_count=1234, incomplete_results=True)

        self.assertIsInstance(page, Page)
        self.assertEqual(list(page), ["a", "b"])
        self.assertEqual(len(page), 2)
        self.assertEqual(page.total_count, 1234)
        self.assertTrue(page.incomplete_results)
        self.assertIsNone(page.next)
