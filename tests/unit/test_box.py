"""Test Main methods."""
import json
from unittest import TestCase

from napps.kytos.storehouse.main import Box, metadata_from_box


class TestBox(TestCase):
    """Tests for the Box class."""

    def setUp(self):
        """Execute steps before each tests."""
        self.box = Box({}, 'storehouse_test', 'box')

    def test__str__(self):
        """Test __str__ method."""
        box_str = '%s.%s' % (self.box.namespace, self.box.box_id)
        self.assertEqual(str(self.box), box_str)

    def test_name_property(self):
        """Test name property."""
        self.assertEqual(self.box.name, 'box')

    def test_from_json(self):
        """Test from_json method."""
        data = '{"data": "a", "namespace": "b", "name": "c"}'
        from_json_box = self.box.from_json(data)
        self.assertEqual(from_json_box.data, 'a')
        self.assertEqual(from_json_box.namespace, 'b')
        self.assertEqual(from_json_box.name, 'c')

    def test_to_dict(self):
        """Test to_dict method."""
        expected_data = {
            "data": self.box.data,
            "namespace": self.box.namespace,
            "owner": self.box.owner,
            "created_at": self.box.created_at,
            "id": self.box.box_id,
            "name": self.box.name
        }
        dict_data = self.box.to_dict()
        self.assertEqual(dict_data, expected_data)

    def test_to_json(self):
        """Test to_json method."""
        data = {
            "data": self.box.data,
            "namespace": self.box.namespace,
            "owner": self.box.owner,
            "created_at": self.box.created_at,
            "id": self.box.box_id,
            "name": self.box.name
        }
        expected_data = json.dumps(data, indent=4)
        json_data = self.box.to_json()
        self.assertEqual(json_data, expected_data)

    def test_metadata_from_box(self):
        """Test metadata_from_box method."""
        expected_metadata = {"box_id": self.box.box_id,
                             "name": self.box.name,
                             "owner": self.box.owner,
                             "created_at": self.box.created_at}
        metadata = metadata_from_box(self.box)
        self.assertEqual(metadata, expected_metadata)
