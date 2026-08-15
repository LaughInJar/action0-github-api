import json
import unittest

from action0.client.testing import StubBackend
from action0.github import CreatePullReview
from action0.github import GitHubClient
from action0.github import ListPullReviews
from action0.github import ListReviewComments
from action0.github import Review
from action0.github import ReviewEvent
from action0.github import ReviewState
from action0.req import Response

REVIEW_PAYLOAD = {
    "id": 80,
    "state": "APPROVED",
    "html_url": "https://github.com/octo/demo/pull/12#pullrequestreview-80",
    "user": None,
    "body": "Looks great.",
}

REVIEW_COMMENT_PAYLOAD = {
    "id": 10,
    "path": "src/app.py",
    "body": "Shouldn't this be a set?",
    "html_url": "https://github.com/octo/demo/pull/12#discussion_r10",
    "line": 28,
}


class ListPullReviewsTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.reviews.ListPullReviews`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the request path and that the array is parsed into a page
        of :py:class:`Review`.
        """
        backend = StubBackend(Response(200, body=json.dumps([REVIEW_PAYLOAD])))
        client = GitHubClient(backend)

        page = client.send(ListPullReviews(owner="octo", repo="demo", pull_number=12))

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/pulls/12/reviews?per_page=30&page=1",
        )
        self.assertEqual([review.state for review in page], [ReviewState.APPROVED])


class CreatePullReviewTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.reviews.CreatePullReview`
    """

    def test_request(self) -> None:
        """
        Test the request shape: POST with the uppercase event value in
        the JSON body.
        """
        request = CreatePullReview(
            owner="octo", repo="demo", pull_number=12, event=ReviewEvent.APPROVE
        ).as_request("https://api.github.com")

        self.assertEqual(request.method, "POST")
        self.assertEqual(
            request.url.as_str(), "https://api.github.com/repos/octo/demo/pulls/12/reviews"
        )
        body = request.body_str()
        assert body is not None
        self.assertEqual(json.loads(body), {"event": "APPROVE"})  # None body omitted

    def test_parses_created_review(self) -> None:
        """
        Test that the payload is parsed into the created
        :py:class:`Review`.
        """
        backend = StubBackend(Response(200, body=json.dumps(REVIEW_PAYLOAD)))
        client = GitHubClient(backend, token="ghp_secret")

        review = client.send(
            CreatePullReview(
                owner="octo",
                repo="demo",
                pull_number=12,
                event=ReviewEvent.COMMENT,
                body="One question inline.",
            )
        )

        self.assertIsInstance(review, Review)
        self.assertEqual(review.id, 80)


class ListReviewCommentsTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.reviews.ListReviewComments`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the request path and that the array is parsed into a page
        of :py:class:`ReviewComment`.
        """
        backend = StubBackend(Response(200, body=json.dumps([REVIEW_COMMENT_PAYLOAD])))
        client = GitHubClient(backend)

        page = client.send(ListReviewComments(owner="octo", repo="demo", pull_number=12))

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/pulls/12/comments?per_page=30&page=1",
        )
        self.assertEqual([comment.line for comment in page], [28])
