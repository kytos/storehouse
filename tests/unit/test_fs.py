"""Test Main methods."""
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from napps.kytos.storehouse.backends.fs import FileSystem, _create_dirs
from napps.kytos.storehouse.main import Box


# pylint: disable=protected-access
class TestFileSystem(TestCase):
    """Tests for the FileSystem class."""

    # pylint: disable=arguments-differ
    @patch('napps.kytos.storehouse.backends.fs.FileSystem._parse_settings')
    def setUp(self, mock_parse_settings):
        """Execute steps before each tests."""
        mock_parse_settings.return_value = MagicMock()
        self.file_system = FileSystem()

    @staticmethod
    @patch('napps.kytos.storehouse.backends.fs.Path')
    def test_create_dirs(mock_path):
        """Test _create_dirs method."""
        _create_dirs('destination')

        mock_path.assert_called_with('destination')
        mock_path.return_value.mkdir.assert_called()

    @patch('napps.kytos.storehouse.backends.fs._create_dirs')
    @patch('os.environ.get', return_value='/')
    def test_parse_settings(self, *args):
        """Test _parse_settings method."""
        (_, mock_create_dirs) = args

        self.file_system._parse_settings()

        calls = [call(self.file_system.destination_path),
                 call(self.file_system.lock_path)]
        mock_create_dirs.assert_has_calls(calls)

    @patch('napps.kytos.storehouse.backends.fs.Path')
    def test_get_destination(self, mock_path):
        """Test _get_destination method."""
        destination = self.file_system._get_destination('namespace')

        mock_path.assert_called_with(self.file_system.destination_path,
                                     'namespace')
        self.assertEqual(destination, mock_path.return_value)

    @patch('pickle.dump')
    @patch('builtins.open')
    @patch('napps.kytos.storehouse.backends.fs.FileLock')
    def test_write_to_file(self, *args):
        """Test _write_to_file method."""
        (_, mock_open, mock_dump) = args
        save_file = MagicMock()
        mock_open.return_value = save_file

        box = MagicMock()
        self.file_system._write_to_file('filename', box)

        mock_dump.assert_called_with(box, save_file.__enter__())

    @patch('pickle.load')
    @patch('builtins.open')
    @patch('napps.kytos.storehouse.backends.fs.FileLock')
    def test_load_from_file(self, *args):
        """Test _load_from_file method."""
        (_, mock_open, mock_load) = args
        load_file = MagicMock()
        mock_open.return_value = load_file
        mock_load.return_value = 'data'

        data = self.file_system._load_from_file('filename')

        mock_load.assert_called_with(load_file.__enter__())
        self.assertEqual(data, 'data')

    def test_delete_file(self):
        """Test _delete_file method to success and failure cases."""
        path = MagicMock()
        path.exists.side_effect = [True, False]
        path.unlink.return_value = 'unlink'
        return_1 = self.file_system._delete_file(path)
        return_2 = self.file_system._delete_file(path)

        self.assertTrue(return_1)
        self.assertFalse(return_2)

    @patch('napps.kytos.storehouse.backends.fs.Path')
    def test_list_namespace_success_case(self, mock_path):
        """Test _list_namespace method to success case."""
        content = []
        for is_dir in [False, False, True]:
            obj = MagicMock()
            obj.name = 'name'
            obj.is_dir.return_value = is_dir
            content.append(obj)

        path = MagicMock()
        path.exists.return_value = True
        path.iterdir.return_value = content
        mock_path.return_value = path
        list_namespace = self.file_system._list_namespace('namespace')

        self.assertEqual(list_namespace, [content[0].name, content[1].name])

    @patch('napps.kytos.storehouse.backends.fs.Path')
    def test_list_namespace_failure_case(self, mock_path):
        """Test _list_namespace method to failure case."""
        path = MagicMock()
        path.exists.return_value = False
        mock_path.return_value = path

        list_namespace = self.file_system._list_namespace('namespace')

        self.assertEqual(list_namespace, [])

    @patch('napps.kytos.storehouse.backends.fs.Path')
    @patch('napps.kytos.storehouse.backends.fs._create_dirs')
    @patch('napps.kytos.storehouse.backends.fs.FileSystem._write_to_file')
    def test_create(self, *args):
        """Test create method."""
        (mock_write_to_file, mock_create_dirs, mock_path) = args
        destination = MagicMock()
        mock_path.return_value = destination

        box = Box('any', 'namespace', box_id='123')
        self.file_system.create(box)

        mock_path.assert_called_with(self.file_system.destination_path,
                                     'namespace')
        mock_create_dirs.assert_called_with(destination)
        mock_write_to_file.assert_called_with(destination.joinpath('123'), box)

    @patch('napps.kytos.storehouse.backends.fs.Path')
    @patch('napps.kytos.storehouse.backends.fs.FileSystem._load_from_file',
           return_value='data')
    def test_retrieve_success_case(self, *args):
        """Test retrieve method to success case."""
        (mock_load_from_file, mock_path) = args
        path = MagicMock()
        destination = MagicMock()
        destination.is_file.return_value = True
        mock_path.return_value = path
        path.joinpath.return_value = destination

        box = Box('any', 'namespace', box_id='123')
        retrieve = self.file_system.retrieve(box.namespace, box.box_id)

        mock_path.assert_called_with(self.file_system.destination_path,
                                     'namespace')
        mock_load_from_file.assert_called_with(destination)
        self.assertEqual(retrieve, 'data')

    @patch('napps.kytos.storehouse.backends.fs.Path')
    def test_retrieve_failure_case(self, mock_path):
        """Test retrieve method to failure case."""
        path = MagicMock()
        destination = MagicMock()
        destination.is_file.return_value = False
        mock_path.return_value = path
        path.joinpath.return_value = destination

        box = Box('any', 'namespace', box_id='123')
        retrieve = self.file_system.retrieve(box.namespace, box.box_id)

        self.assertFalse(retrieve)

    @patch('napps.kytos.storehouse.backends.fs.Path')
    @patch('napps.kytos.storehouse.backends.fs.FileSystem._write_to_file')
    def test_update(self, *args):
        """Test update method."""
        (mock_write, mock_path) = args
        destination = MagicMock()
        mock_path.return_value = destination

        box = Box('any', 'namespace', box_id='123')
        self.file_system.update(box.namespace, box)

        mock_path.assert_called_with(self.file_system.destination_path,
                                     'namespace')
        destination.joinpath.assert_called_with('123')
        mock_write.assert_called_with(destination.joinpath.return_value, box)

    @patch('napps.kytos.storehouse.backends.fs.Path')
    @patch('napps.kytos.storehouse.backends.fs.FileSystem._delete_file')
    def test_delete(self, *args):
        """Test delete method."""
        (mock_delete_file, mock_path) = args
        path = MagicMock()
        destination = MagicMock()
        mock_path.return_value = path
        path.joinpath.return_value = destination

        box = Box('any', 'namespace', box_id='123')
        self.file_system.delete(box.namespace, box.box_id)

        mock_path.assert_called_with(self.file_system.destination_path,
                                     'namespace')
        path.joinpath.assert_called_with('123')
        mock_delete_file.assert_called_with(destination)

    @patch('napps.kytos.storehouse.backends.fs.FileSystem._list_namespace')
    def test_list(self, mock_list_namespace):
        """Test list method."""
        list_namespace = self.file_system.list('namespace')

        mock_list_namespace.assert_called_with('namespace')
        self.assertEqual(list_namespace, mock_list_namespace.return_value)

    @patch('napps.kytos.storehouse.backends.fs.Path')
    def test_list_namespaces_success_case(self, mock_path):
        """Test list_namespaces method to success case."""
        content = []
        for is_dir in [False, False, True]:
            obj = MagicMock()
            obj.name = 'name'
            obj.is_dir.return_value = is_dir
            content.append(obj)

        path = MagicMock()
        path.exists.return_value = True
        path.iterdir.return_value = content
        mock_path.return_value = path
        list_namespace = self.file_system.list_namespaces()

        mock_path.assert_called_with(self.file_system.destination_path, '.')
        self.assertEqual(list_namespace, [content[2].name])

    @patch('napps.kytos.storehouse.backends.fs.Path')
    def test_list_namespaces_failure_case(self, mock_path):
        """Test list_namespaces method to failure case."""
        path = MagicMock()
        path.exists.return_value = False
        mock_path.return_value = path

        list_namespace = self.file_system.list_namespaces()

        mock_path.assert_called_with(self.file_system.destination_path, '.')
        self.assertEqual(list_namespace, [])

    @patch('napps.kytos.storehouse.backends.fs.FileSystem.retrieve')
    @patch('napps.kytos.storehouse.backends.fs.FileSystem.list')
    @patch('napps.kytos.storehouse.backends.fs.FileSystem.list_namespaces',
           return_value=['namespace'])
    def test_backup_without_box_id(self, *args):
        """Test backup method without box_id parameter."""
        (_, mock_list, mock_retrieve) = args

        mock_list.return_value = ['456']

        retrieve = MagicMock()
        retrieve.to_json.return_value = {}
        mock_retrieve.return_value = retrieve

        box = Box('any', 'namespace', box_id='123')
        boxes_dict_1 = self.file_system.backup(box.namespace, box.box_id)
        boxes_dict_2 = self.file_system.backup(box.namespace)

        self.assertEqual(boxes_dict_1, {'123': {}})
        self.assertEqual(boxes_dict_2, {'456': {}})
