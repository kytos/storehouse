"""Test Main methods."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from napps.kytos.storehouse.backends.etcd import (Etcd, join_fullname,
                                                  split_fullname)
from napps.kytos.storehouse.main import Box


# pylint: disable=protected-access, unused-argument, no-member
class TestEtcd(TestCase):
    """Tests for the Etcd class."""

    # pylint: disable=arguments-differ
    @patch('napps.kytos.storehouse.backends.etcd.etcd3.client')
    def setUp(self, mock_client):
        """Execute steps before each tests."""
        mock_client.return_value = MagicMock()
        self.base = Etcd()

        # 'metadata' is the name of the one of objects obtained at tuple
        # returned by the etcd get_all method.
        self.metadata = MagicMock()
        self.metadata.key = b'namespace.123'
        self.base.etcd.get_all.return_value = [(b'', self.metadata)]

    def test_get_all_keys(self):
        """Test _get_all_keys method."""
        all_keys = self.base._get_all_keys()

        self.assertEqual(b'namespace.123', next(all_keys))

    @patch('pickle.dumps', return_value='raw_data')
    def test_create(self, mock_dumps):
        """Test create method."""
        box = Box('any', 'namespace', box_id='123')
        self.base.create(box)

        self.base.etcd.put.assert_called_with('namespace.123', 'raw_data')

    @patch('pickle.loads', return_value='data')
    def test_retrieve_success_case(self, mock_loads):
        """Test retrieve method to success case."""
        self.base.etcd.get.return_value = ('raw_data', '')

        box = Box('any', 'namespace', box_id='123')
        retrieve = self.base.retrieve(box.namespace, box.box_id)

        self.base.etcd.get.assert_called_with('namespace.123')
        self.assertEqual(retrieve, 'data')

    def test_retrieve_failure_case(self):
        """Test retrieve method to failure case."""
        self.base.etcd.get.return_value = (None, '')

        box = Box('any', 'namespace', box_id='123')
        retrieve = self.base.retrieve(box.namespace, box.box_id)

        self.base.etcd.get.assert_called_with('namespace.123')
        self.assertIsNone(retrieve)

    def test_delete(self):
        """Test delete method."""
        box = Box('any', 'namespace', box_id='123')
        self.base.delete(box.namespace, box.box_id)

        self.base.etcd.delete.assert_called_with('namespace.123')

    def test_list(self):
        """Test list method."""
        obj = MagicMock()
        obj.key = b'namespace.123'
        self.base.etcd.get_prefix.return_value = [('', obj)]

        list_return = self.base.list('namespace')

        self.base.etcd.get_prefix.assert_called_with('namespace',
                                                     keys_only=True)
        self.assertEqual(next(list_return), b'123')

    def test_list_namespaces(self):
        """Test list_namespaces method."""
        namespaces = self.base.list_namespaces()

        self.assertEqual(namespaces, {b'namespace'})

    @patch('pickle.loads')
    def test_backup(self, mock_loads):
        """Test backup method."""
        next(self.base.backup())

        mock_loads.assert_called_with((b'', self.metadata))

    def test_split_fullname(self):
        """Test split_fullname method."""
        fullname = b'namespace.box_id'

        split = split_fullname(fullname)

        self.assertEqual(split, [b'namespace', b'box_id'])

    def test_join_fullname(self):
        """Test join_fullname method to binary and string parameters."""
        fullname_1 = join_fullname(b'namespace', b'box_id')
        self.assertEqual(fullname_1, b'namespace.box_id')

        fullname_2 = join_fullname('namespace', 'box_id')
        self.assertEqual(fullname_2, 'namespace.box_id')
