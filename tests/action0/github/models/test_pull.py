import unittest
from datetime import datetime
from datetime import timezone

from action0.github import IssueState
from action0.github import PullRequest
from action0.github import PullRequestRef

USER_PAYLOAD = {
    "login": "octocat",
    "id": 1,
    "html_url": "https://github.com/octocat",
    "type": "User",
}

REPO_PAYLOAD = {
    "id": 7,
    "name": "demo",
    "full_name": "octo/demo",
    "owner": USER_PAYLOAD,
    "private": False,
    "html_url": "https://github.com/octo/demo",
    "default_branch": "main",
}

HEAD_PAYLOAD = {
    "label": "octocat:new-topic",
    "ref": "new-topic",
    "sha": "aa218f56b14c9653891f9e74264a383fa43fefbd",
    "user": USER_PAYLOAD,
    "repo": REPO_PAYLOAD,
}

BASE_PAYLOAD = {
    "label": "octo:main",
    "ref": "main",
    "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
    "user": USER_PAYLOAD,
    "repo": REPO_PAYLOAD,
}

PULL_PAYLOAD = {
    "id": 201,
    "number": 1347,
    "title": "Amazing new feature",
    "state": "open",
    "html_url": "https://github.com/octo/demo/pull/1347",
    "head": HEAD_PAYLOAD,
    "base": BASE_PAYLOAD,
    "user": USER_PAYLOAD,
    "body": "Please pull these awesome changes in!",
    "labels": [{"id": 1, "name": "bug", "color": "f29513"}],
    "assignees": [USER_PAYLOAD],
    "requested_reviewers": [USER_PAYLOAD],
    "draft": True,
    "locked": False,
    "merge_commit_sha": "e5bd3914e2e596debea16f433f57875b5b90bcd6",
    "created_at": "2026-08-01T10:00:00Z",
    "updated_at": "2026-08-02T10:00:00Z",
    "closed_at": None,
    "merged_at": None,
}


class PullRequestRefTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.pull.PullRequestRef`
    """

    def test_from_json(self) -> None:
        """
        Test that a head/base payload is mapped onto the dataclass,
        including the nested user and repository.
        """
        ref = PullRequestRef.from_json(HEAD_PAYLOAD)

        self.assertEqual(ref.label, "octocat:new-topic")
        self.assertEqual(ref.ref, "new-topic")
        self.assertEqual(ref.sha, "aa218f56b14c9653891f9e74264a383fa43fefbd")
        assert ref.user is not None
        self.assertEqual(ref.user.login, "octocat")
        assert ref.repo is not None
        self.assertEqual(ref.repo.full_name, "octo/demo")

    def test_from_json_deleted_fork(self) -> None:
        """
        Test that a null ``repo``/``user`` (the fork was deleted after
        the pull request was opened) maps to ``None``.
        """
        ref = PullRequestRef.from_json(dict(HEAD_PAYLOAD, user=None, repo=None))

        self.assertIsNone(ref.user)
        self.assertIsNone(ref.repo)


class PullRequestTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.pull.PullRequest`
    """

    def test_from_json(self) -> None:
        """
        Test that a listing (``pull-request-simple``) payload is mapped
        onto the dataclass; the statistics only the individual fetch
        carries stay ``None``.
        """
        pull = PullRequest.from_json(PULL_PAYLOAD)

        self.assertEqual(pull.number, 1347)
        self.assertEqual(pull.state, IssueState.OPEN)
        self.assertEqual(pull.head.ref, "new-topic")
        self.assertEqual(pull.base.ref, "main")
        assert pull.user is not None
        self.assertEqual(pull.user.login, "octocat")
        self.assertEqual([label.name for label in pull.labels], ["bug"])
        self.assertEqual([reviewer.login for reviewer in pull.requested_reviewers], ["octocat"])
        self.assertTrue(pull.draft)
        self.assertEqual(pull.created_at, datetime(2026, 8, 1, 10, tzinfo=timezone.utc))
        self.assertIsNone(pull.mergeable)
        self.assertIsNone(pull.commits)
        self.assertIsNone(pull.changed_files)

    def test_from_json_full(self) -> None:
        """
        Test that a full (``pull-request``) payload fills the
        merge/diff statistics.
        """
        payload = dict(
            PULL_PAYLOAD,
            mergeable=True,
            commits=3,
            additions=100,
            deletions=3,
            changed_files=5,
        )

        pull = PullRequest.from_json(payload)

        self.assertTrue(pull.mergeable)
        self.assertEqual(pull.commits, 3)
        self.assertEqual(pull.additions, 100)
        self.assertEqual(pull.deletions, 3)
        self.assertEqual(pull.changed_files, 5)

    def test_is_merged(self) -> None:
        """
        Test that ``is_merged`` derives from ``merged_at`` — a merged
        pull request is ``closed`` with a merge timestamp.
        """
        open_pull = PullRequest.from_json(PULL_PAYLOAD)
        merged_pull = PullRequest.from_json(
            dict(
                PULL_PAYLOAD,
                state="closed",
                closed_at="2026-08-03T10:00:00Z",
                merged_at="2026-08-03T10:00:00Z",
            )
        )

        self.assertFalse(open_pull.is_merged)
        self.assertTrue(merged_pull.is_merged)
        self.assertEqual(merged_pull.state, IssueState.CLOSED)
        self.assertEqual(merged_pull.merged_at, datetime(2026, 8, 3, 10, tzinfo=timezone.utc))

    def test_from_json_minimal(self) -> None:
        """
        Test that a payload with only the required keys maps the
        optional fields to their defaults.
        """
        pull = PullRequest.from_json(
            {
                "id": 1,
                "number": 2,
                "title": "Ghost pull request",
                "state": "closed",
                "html_url": "https://github.com/octo/demo/pull/2",
                "head": dict(HEAD_PAYLOAD, user=None, repo=None),
                "base": BASE_PAYLOAD,
                "user": None,
            }
        )

        self.assertIsNone(pull.user)
        self.assertIsNone(pull.body)
        self.assertEqual(pull.labels, [])
        self.assertEqual(pull.assignees, [])
        self.assertEqual(pull.requested_reviewers, [])
        self.assertFalse(pull.draft)
        self.assertFalse(pull.locked)
        self.assertIsNone(pull.merge_commit_sha)
        self.assertIsNone(pull.created_at)
        self.assertFalse(pull.is_merged)
