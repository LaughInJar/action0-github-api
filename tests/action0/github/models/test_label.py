import unittest

from action0.github import Label


class LabelTestCase(unittest.TestCase):
    """
    tests for :py:class:`action0.github.models.label.Label`
    """

    def test_from_json_object(self) -> None:
        """
        Test that a full label object is mapped onto the dataclass.
        """
        label = Label.from_json(
            {
                "id": 208045946,
                "name": "bug",
                "color": "f29513",
                "description": "Something isn't working",
                "default": True,
                "node_id": "MDU6TGFiZWwyMDgwNDU5NDY=",  # unknown keys are ignored
            }
        )

        self.assertEqual(
            label,
            Label(
                name="bug",
                id=208045946,
                color="f29513",
                description="Something isn't working",
                default=True,
            ),
        )

    def test_from_json_bare_string(self) -> None:
        """
        Test that a bare label name (as some payloads contain) becomes a
        name-only label.
        """
        self.assertEqual(Label.from_json("bug"), Label(name="bug"))
