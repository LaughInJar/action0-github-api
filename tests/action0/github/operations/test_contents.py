import base64
import json
import unittest

from action0.client.testing import StubBackend
from action0.github import ContentFile
from action0.github import DirectoryEntry
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
