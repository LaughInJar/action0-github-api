import unittest

from action0.github import Page


class PageTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.page.Page`
    """

    def test_behaves_like_a_sequence(self) -> None:
        """
        Test that a page supports iteration, ``len``, indexing, slicing
        and membership like the list of its items.
        """
        page = Page(items=["a", "b", "c"])

        self.assertEqual(list(page), ["a", "b", "c"])
        self.assertEqual(len(page), 3)
        self.assertEqual(page[1], "b")
        self.assertEqual(page[1:], ["b", "c"])
        self.assertIn("a", page)
        self.assertIsNone(page.next)

    def test_truthiness(self) -> None:
        """
        Test that an empty page is falsy, a filled one truthy — so
        ``while page:`` loops read naturally.
        """
        self.assertFalse(Page(items=[]))
        self.assertTrue(Page(items=[1]))
