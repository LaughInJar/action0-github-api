import unittest

from action0.github.operations.links import links
from action0.req import Response

GITHUB_LINK_HEADER = (
    '<https://api.github.com/repositories/1/issues?page=2>; rel="next", '
    '<https://api.github.com/repositories/1/issues?page=5>; rel="last"'
)


class LinksTestCase(unittest.TestCase):
    """
    tests for :py:func:`action0.github.operations.links.links`
    """

    def test_github_style_header(self) -> None:
        """
        Test that GitHub's comma-separated Link header parses into a
        rel-to-URL mapping.
        """
        response = Response(200, headers={"Link": GITHUB_LINK_HEADER})

        self.assertEqual(
            links(response),
            {
                "next": "https://api.github.com/repositories/1/issues?page=2",
                "last": "https://api.github.com/repositories/1/issues?page=5",
            },
        )

    def test_no_link_header(self) -> None:
        """
        Test that a response without a Link header yields no relations.
        """
        self.assertEqual(links(Response(200)), {})

    def test_multiple_link_headers_and_extra_params(self) -> None:
        """
        Test that repeated Link header lines merge and non-rel parameters
        are ignored.
        """
        response = Response(200)
        response.headers.add("Link", '<https://example.com/a?page=2>; title="x"; rel="next"')
        response.headers.add("Link", "<https://example.com/a?page=9>; rel=last")

        self.assertEqual(
            links(response),
            {"next": "https://example.com/a?page=2", "last": "https://example.com/a?page=9"},
        )
