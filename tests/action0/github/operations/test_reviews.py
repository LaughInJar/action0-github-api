import json
import unittest

from action0.client.testing import StubBackend
from action0.github import CreatePullReview
from action0.github import CreateReviewComment
from action0.github import DraftReviewComment
from action0.github import GitHubClient
from action0.github import ListPullReviews
from action0.github import ListReviewComments
from action0.github import PullRequest
from action0.github import RemoveRequestedReviewers
from action0.github import RequestReviewers
from action0.github import Review
from action0.github import ReviewComment
from action0.github import ReviewEvent
from action0.github import ReviewSide
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


class CreatePullReviewBatchTestCase(unittest.TestCase):
    """
    tests for the ``comments`` batch of
    :py:class:`action0.github.operations.reviews.CreatePullReview`
    """

    def test_request_serializes_draft_comments(self) -> None:
        """
        Test that :py:class:`DraftReviewComment` entries serialize into
        GitHub's ``comments`` array — ``None`` fields omitted, enums as
        their values.
        """
        request = CreatePullReview(
            owner="octo",
            repo="demo",
            pull_number=12,
            event=ReviewEvent.REQUEST_CHANGES,
            body="Two problems inline.",
            commit_id="ecdd80bb",
            comments=[
                DraftReviewComment(path="src/app.py", body="Off by one.", line=28),
                DraftReviewComment(
                    path="src/app.py",
                    body="This whole block reads twice.",
                    line=40,
                    side=ReviewSide.RIGHT,
                    start_line=35,
                ),
            ],
        ).as_request("https://api.github.com")

        body = request.body_str()
        assert body is not None
        self.assertEqual(
            json.loads(body),
            {
                "event": "REQUEST_CHANGES",
                "body": "Two problems inline.",
                "commit_id": "ecdd80bb",
                "comments": [
                    {"path": "src/app.py", "body": "Off by one.", "line": 28},
                    {
                        "path": "src/app.py",
                        "body": "This whole block reads twice.",
                        "line": 40,
                        "side": "RIGHT",
                        "start_line": 35,
                    },
                ],
            },
        )


class CreateReviewCommentTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.reviews.CreateReviewComment`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the standalone line comment: ``file_path`` goes on the
        wire as ``path``, and the answer parses.
        """
        backend = StubBackend(Response(201, body=json.dumps(REVIEW_COMMENT_PAYLOAD)))
        client = GitHubClient(backend, token="ghp_secret")

        comment = client.send(
            CreateReviewComment(
                owner="octo",
                repo="demo",
                pull_number=12,
                body="Shouldn't this be a set?",
                commit_id="ecdd80bb",
                file_path="src/app.py",
                line=28,
                side=ReviewSide.RIGHT,
            )
        )

        request = backend.requests[0]
        self.assertEqual(request.method, "POST")
        body = request.body_str()
        assert body is not None
        self.assertEqual(
            json.loads(body),
            {
                "body": "Shouldn't this be a set?",
                "commit_id": "ecdd80bb",
                "path": "src/app.py",
                "line": 28,
                "side": "RIGHT",
            },
        )
        self.assertIsInstance(comment, ReviewComment)


class RequestReviewersTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.reviews.RequestReviewers`
    and :py:class:`action0.github.operations.reviews.RemoveRequestedReviewers`
    """

    PULL_PAYLOAD = {
        "id": 201,
        "number": 12,
        "title": "Amazing new feature",
        "state": "open",
        "html_url": "https://github.com/octo/demo/pull/12",
        "head": {"label": "octo:topic", "ref": "topic", "sha": "aa218f56"},
        "base": {"label": "octo:main", "ref": "main", "sha": "6dcb09b5"},
        "requested_reviewers": [{"login": "octocat", "id": 1, "html_url": "…", "type": "User"}],
    }

    def test_request_and_parse(self) -> None:
        """
        Test the POST body and the updated ``requested_reviewers``.
        """
        backend = StubBackend(Response(201, body=json.dumps(self.PULL_PAYLOAD)))
        client = GitHubClient(backend, token="ghp_secret")

        pull = client.send(
            RequestReviewers(owner="octo", repo="demo", pull_number=12, reviewers=["octocat"])
        )

        body = backend.requests[0].body_str()
        assert body is not None
        self.assertEqual(json.loads(body), {"reviewers": ["octocat"]})
        self.assertIsInstance(pull, PullRequest)
        self.assertEqual([user.login for user in pull.requested_reviewers], ["octocat"])

    def test_remove_is_delete_with_body(self) -> None:
        """
        Test that the withdrawal is a DELETE carrying the JSON body.
        """
        backend = StubBackend(Response(200, body=json.dumps(self.PULL_PAYLOAD)))
        client = GitHubClient(backend, token="ghp_secret")

        client.send(
            RemoveRequestedReviewers(
                owner="octo", repo="demo", pull_number=12, reviewers=["octocat"]
            )
        )

        request = backend.requests[0]
        self.assertEqual(request.method, "DELETE")
        body = request.body_str()
        assert body is not None
        self.assertEqual(json.loads(body), {"reviewers": ["octocat"]})
