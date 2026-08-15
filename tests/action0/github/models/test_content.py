import base64
import unittest

from action0.github import ContentFile
from action0.github import ContentType
from action0.github import DirectoryEntry

FILE_PAYLOAD = {
    "name": "hello.py",
    "path": "src/hello.py",
    "sha": "3d21ec53a331a6f037a91c368710b99387d012c1",
    "size": 18,
    "type": "file",
    "encoding": "base64",
    "content": base64.b64encode(b'print("hi there")\n').decode("ascii"),
    "html_url": "https://github.com/octo/demo/blob/main/src/hello.py",
    "download_url": "https://raw.githubusercontent.com/octo/demo/main/src/hello.py",
}


class ContentFileTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.content.ContentFile`
    """

    def test_from_json_and_decoding(self) -> None:
        """
        Test that the payload is parsed and the base64 content decodes
        via :py:attr:`decoded` and :py:attr:`text`.
        """
        file = ContentFile.from_json(FILE_PAYLOAD)

        self.assertEqual(file.type, ContentType.FILE)
        self.assertEqual(file.path, "src/hello.py")
        self.assertEqual(file.decoded, b'print("hi there")\n')
        self.assertEqual(file.text, 'print("hi there")\n')

    def test_decoded_without_inlined_content(self) -> None:
        """
        Test that :py:attr:`decoded` refuses a payload without inlined
        bytes (GitHub sends ``encoding: "none"`` for 1-100 MB files).
        """
        file = ContentFile.from_json(dict(FILE_PAYLOAD, encoding="none", content=""))

        with self.assertRaises(ValueError):
            file.decoded


class DirectoryEntryTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.content.DirectoryEntry`
    """

    def test_from_json(self) -> None:
        """
        Test that a directory's entry parses — no ``download_url`` for
        subdirectories.
        """
        entry = DirectoryEntry.from_json(
            {
                "name": "src",
                "path": "src",
                "sha": "9a2f...",
                "size": 0,
                "type": "dir",
                "download_url": None,
            }
        )

        self.assertEqual(entry.type, ContentType.DIR)
        self.assertIsNone(entry.download_url)
