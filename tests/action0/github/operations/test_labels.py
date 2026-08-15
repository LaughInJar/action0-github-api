import json
import unittest

from action0.client.testing import StubBackend
from action0.github import AddIssueLabels
from action0.github import CreateLabel
from action0.github import DeleteLabel
from action0.github import GitHubClient
from action0.github import Label
from action0.github import ListRepoLabels
from action0.github import RemoveIssueLabel
from action0.github import UpdateLabel
from action0.req import Response

LABEL_PAYLOAD = {"id": 1, "name": "bug", "color": "f29513", "default": True}


class ListRepoLabelsTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.labels.ListRepoLabels`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the request path and that the array is parsed into a page
        of :py:class:`Label`.
        """
        backend = StubBackend(Response(200, body=json.dumps([LABEL_PAYLOAD])))
        client = GitHubClient(backend)

        page = client.send(ListRepoLabels(owner="octo", repo="demo"))

        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/labels?per_page=30&page=1",
        )
        self.assertEqual([label.name for label in page], ["bug"])


class AddIssueLabelsTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.labels.AddIssueLabels`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the POST body and that the answer (the complete label set)
        is parsed into the label list.
        """
        payload = [LABEL_PAYLOAD, {"id": 2, "name": "ui", "color": "bfd4f2"}]
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend, token="ghp_secret")

        labels = client.send(
            AddIssueLabels(owner="octo", repo="demo", issue_number=1347, labels=["ui"])
        )

        request = backend.requests[0]
        self.assertEqual(request.method, "POST")
        body = request.body_str()
        assert body is not None
        self.assertEqual(json.loads(body), {"labels": ["ui"]})
        self.assertEqual([label.name for label in labels], ["bug", "ui"])
        self.assertIsInstance(labels[0], Label)


class RemoveIssueLabelTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.labels.RemoveIssueLabel`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the DELETE request — a label name with a space is
        percent-encoded into the path — and the remaining set parsing.
        """
        backend = StubBackend(Response(200, body=json.dumps([LABEL_PAYLOAD])))
        client = GitHubClient(backend, token="ghp_secret")

        labels = client.send(
            RemoveIssueLabel(owner="octo", repo="demo", issue_number=1347, name="help wanted")
        )

        request = backend.requests[0]
        self.assertEqual(request.method, "DELETE")
        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/issues/1347/labels/help%20wanted",
        )
        self.assertEqual([label.name for label in labels], ["bug"])


class CreateLabelTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.labels.CreateLabel`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the POST body (``None`` color omitted — GitHub picks one)
        and the parsing.
        """
        backend = StubBackend(Response(201, body=json.dumps(LABEL_PAYLOAD)))
        client = GitHubClient(backend, token="ghp_secret")

        label = client.send(
            CreateLabel(owner="octo", repo="demo", name="bug", description="Something broke")
        )

        request = backend.requests[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.url.as_str(), "https://api.github.com/repos/octo/demo/labels")
        body = request.body_str()
        assert body is not None
        self.assertEqual(json.loads(body), {"name": "bug", "description": "Something broke"})
        self.assertEqual(label.name, "bug")


class UpdateLabelTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.labels.UpdateLabel`
    """

    def test_request_renames(self) -> None:
        """
        Test the PATCH shape: the current name addresses the label in
        the path, the rename travels as ``new_name``.
        """
        request = UpdateLabel(owner="octo", repo="demo", name="bug", new_name="defect").as_request(
            "https://api.github.com"
        )

        self.assertEqual(request.method, "PATCH")
        self.assertEqual(request.url.as_str(), "https://api.github.com/repos/octo/demo/labels/bug")
        body = request.body_str()
        assert body is not None
        self.assertEqual(json.loads(body), {"new_name": "defect"})


class DeleteLabelTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.labels.DeleteLabel`
    """

    def test_request_and_none_result(self) -> None:
        """
        Test the no-content round trip.
        """
        backend = StubBackend(Response(204))
        client = GitHubClient(backend, token="ghp_secret")

        result = client.send(DeleteLabel(owner="octo", repo="demo", name="bug"))

        self.assertEqual(backend.requests[0].method, "DELETE")
        self.assertEqual(
            backend.requests[0].url.as_str(),
            "https://api.github.com/repos/octo/demo/labels/bug",
        )
        self.assertIsNone(result)
