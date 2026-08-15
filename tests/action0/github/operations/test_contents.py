import base64
import json
import unittest

from action0.client.testing import StubBackend
from action0.github import ContentFile
from action0.github import CreateOrUpdateFile
from action0.github import DeleteFile
from action0.github import DirectoryEntry
from action0.github import FileCommit
from action0.github import GetContent
from action0.github import GetReadme
from action0.github import GitHubClient
from action0.req import Response

FILE_PAYLOAD = {
    "name": "hello.py",
    "path": "src/hello.py",
    "sha": "3d21ec53a331a6f037a91c368710b99387d012c1",
    "size": 18,
    "type": "file",
    "encoding": "base64",
    "content": base64.b64encode(b'print("hi there")\n').decode("ascii"),
}

DIRECTORY_PAYLOAD = [
    {"name": "hello.py", "path": "src/hello.py", "sha": "3d21ec5", "size": 18, "type": "file"},
    {"name": "lib", "path": "src/lib", "sha": "9a2f7b1", "size": 0, "type": "dir"},
]


class GetContentTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.contents.GetContent`
    """

    def test_request_with_ref(self) -> None:
        """
        Test the request shape: the repository path lands in the URL
        path (slashes intact), the ``ref`` in the query.
        """
        request = GetContent(
            owner="octo", repo="demo", file_path="src/hello.py", ref="v1.0.0"
        ).as_request("https://api.github.com")

        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/contents/src/hello.py?ref=v1.0.0",
        )

    def test_parses_file_payload(self) -> None:
        """
        Test that an object payload (a file) is parsed into a
        :py:class:`ContentFile`, ready to decode.
        """
        backend = StubBackend(Response(200, body=json.dumps(FILE_PAYLOAD)))
        client = GitHubClient(backend)

        content = client.send(GetContent(owner="octo", repo="demo", file_path="src/hello.py"))

        assert isinstance(content, ContentFile)  # narrows the union for the type checkers
        self.assertEqual(content.text, 'print("hi there")\n')

    def test_parses_directory_payload(self) -> None:
        """
        Test that an array payload (a directory) is parsed into the list
        of :py:class:`DirectoryEntry`.
        """
        backend = StubBackend(Response(200, body=json.dumps(DIRECTORY_PAYLOAD)))
        client = GitHubClient(backend)

        content = client.send(GetContent(owner="octo", repo="demo", file_path="src"))

        assert isinstance(content, list)
        self.assertEqual([entry.name for entry in content], ["hello.py", "lib"])
        self.assertIsInstance(content[0], DirectoryEntry)


class GetReadmeTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.contents.GetReadme`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the request path and that the payload parses into a
        :py:class:`ContentFile`.
        """
        payload = dict(FILE_PAYLOAD, name="README.md", path="README.md")
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend)

        readme = client.send(GetReadme(owner="octo", repo="demo"))

        self.assertEqual(
            backend.requests[0].url.as_str(), "https://api.github.com/repos/octo/demo/readme"
        )
        self.assertEqual(readme.name, "README.md")
        self.assertEqual(readme.decoded, b'print("hi there")\n')


FILE_COMMIT_PAYLOAD = {
    "content": dict(FILE_PAYLOAD, sha="new0sha"),
    "commit": {
        "sha": "7638417db6d59f3c431d3e1f261cc637155684cd",
        "html_url": "https://github.com/octo/demo/commit/7638417d",
        "message": "Add hello.py",
        "author": {"name": "Mona", "email": "mona@github.com", "date": "2026-08-15T10:00:00Z"},
        "parents": [{"sha": "6dcb09b5"}],
    },
}


class CreateOrUpdateFileTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.contents.CreateOrUpdateFile`
    """

    def test_request_encodes_content(self) -> None:
        """
        Test that the raw bytes are base64-encoded into the JSON body
        (the ``serialize=`` field hook) and the create case sends no
        ``sha``.
        """
        request = CreateOrUpdateFile(
            owner="octo",
            repo="demo",
            file_path="src/hello.py",
            message="Add hello.py",
            content=b'print("hi there")\n',
        ).as_request("https://api.github.com")

        self.assertEqual(request.method, "PUT")
        self.assertEqual(
            request.url.as_str(),
            "https://api.github.com/repos/octo/demo/contents/src/hello.py",
        )
        body = request.body_str()
        assert body is not None
        self.assertEqual(
            json.loads(body),
            {
                "message": "Add hello.py",
                "content": base64.b64encode(b'print("hi there")\n').decode("ascii"),
            },
        )

    def test_update_and_parse(self) -> None:
        """
        Test that an update sends the blob sha and the answer parses
        into a :py:class:`FileCommit` carrying the fresh file entry.
        """
        backend = StubBackend(Response(200, body=json.dumps(FILE_COMMIT_PAYLOAD)))
        client = GitHubClient(backend, token="ghp_secret")

        written = client.send(
            CreateOrUpdateFile(
                owner="octo",
                repo="demo",
                file_path="src/hello.py",
                message="Tweak hello.py",
                content=b'print("hello")\n',
                sha="3d21ec53a331a6f037a91c368710b99387d012c1",
            )
        )

        body = backend.requests[0].body_str()
        assert body is not None
        self.assertEqual(json.loads(body)["sha"], "3d21ec53a331a6f037a91c368710b99387d012c1")
        self.assertIsInstance(written, FileCommit)
        assert written.content is not None
        self.assertEqual(written.content.sha, "new0sha")  # what the next update needs
        self.assertEqual(written.commit.message, "Add hello.py")
        assert written.commit.author is not None
        self.assertEqual(written.commit.author.name, "Mona")


class DeleteFileTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.operations.contents.DeleteFile`
    """

    def test_request_and_parse(self) -> None:
        """
        Test the DELETE-with-JSON-body request and that the answer's
        null ``content`` stays ``None``.
        """
        payload = dict(FILE_COMMIT_PAYLOAD, content=None)
        backend = StubBackend(Response(200, body=json.dumps(payload)))
        client = GitHubClient(backend, token="ghp_secret")

        deleted = client.send(
            DeleteFile(
                owner="octo",
                repo="demo",
                file_path="src/hello.py",
                message="Remove hello.py",
                sha="3d21ec53a331a6f037a91c368710b99387d012c1",
            )
        )

        request = backend.requests[0]
        self.assertEqual(request.method, "DELETE")
        body = request.body_str()
        assert body is not None
        self.assertEqual(
            json.loads(body),
            {"message": "Remove hello.py", "sha": "3d21ec53a331a6f037a91c368710b99387d012c1"},
        )
        self.assertIsNone(deleted.content)
        self.assertEqual(deleted.commit.parents, ["6dcb09b5"])
