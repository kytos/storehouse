"""Test Main methods."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from kytos.lib.helpers import (get_controller_mock, get_kytos_event_mock,
                               get_test_client)
from napps.kytos.storehouse.main import Box


# pylint: disable=protected-access, unused-argument, no-member
class TestMain(TestCase):
    """Tests for the Main class."""

    API_URL = "http://127.0.0.1:8181/api/kytos/storehouse"

    # pylint: disable=arguments-differ
    @patch('napps.kytos.storehouse.main.Main.create_cache')
    @patch('napps.kytos.storehouse.backends.fs.FileSystem')
    @patch('napps.kytos.storehouse.backends.etcd.Etcd')
    def setUp(self, *args):
        """Execute steps before each tests."""
        (mock_etcd, mock_fs, _) = args
        mock_fs.return_value = MagicMock()
        mock_etcd.return_value = MagicMock()

        patch('kytos.core.helpers.run_on_thread', lambda x: x).start()
        # pylint: disable=import-outside-toplevel
        from napps.kytos.storehouse.main import Main
        self.addCleanup(patch.stopall)

        self.napp = Main(get_controller_mock())

    @patch('napps.kytos.storehouse.main.log')
    def test_shutdown(self, mock_log):
        """Test shutdown method."""
        self.napp.shutdown()

        mock_log.info.assert_called_once()

    def test_create_cache(self):
        """Test create_cache method."""
        box = Box('any', 'namespace', 'ABC', '123')
        self.napp.backend.list_namespaces.return_value = ['namespace']
        self.napp.backend.list.return_value = ['123']
        self.napp.backend.retrieve.return_value = box

        self.napp.create_cache()

        box_metadata = self.napp.metadata_cache['namespace'][0]
        self.assertEqual(box_metadata['box_id'], box.box_id)
        self.assertEqual(box_metadata['name'], box.name)
        self.assertEqual(box_metadata['owner'], box.owner)
        self.assertEqual(box_metadata['created_at'], box.created_at)

    def test_delete_metadata_from_cache_by_box_id(self):
        """Test delete_metadata_from_cache method using box_id."""
        self.napp.metadata_cache = {'namespace': [{'box_id': '1'}]}
        self.napp.delete_metadata_from_cache('namespace', box_id='1')
        self.assertEqual(self.napp.metadata_cache, {'namespace': []})

    def test_delete_metadata_from_cache_by_name(self):
        """Test delete_metadata_from_cache method using name."""
        self.napp.metadata_cache = {'namespace': [{'name': 'n'}]}
        self.napp.delete_metadata_from_cache('namespace', name='n')
        self.assertEqual(self.napp.metadata_cache, {'namespace': []})

    def test_add_metadata_to_cache(self):
        """Test add_metadata_to_cache method."""
        box = Box('any', 'namespace', 'ABC', '123')
        self.napp.add_metadata_to_cache(box)

        box_metadata = self.napp.metadata_cache['namespace'][0]
        self.assertEqual(box_metadata['box_id'], box.box_id)
        self.assertEqual(box_metadata['name'], box.name)
        self.assertEqual(box_metadata['owner'], box.owner)
        self.assertEqual(box_metadata['created_at'], box.created_at)

    def test_search_metadata_by(self):
        """Test search_metadata_by method."""
        self.napp.metadata_cache = {'namespace': [{'box_id': '123'}]}

        results_1 = self.napp.search_metadata_by('namespace', query='123')
        results_2 = self.napp.search_metadata_by('namespace', query='456')

        self.assertEqual(results_1, [{'box_id': '123'}])
        self.assertEqual(results_2, [])

    @patch('napps.kytos.storehouse.main.Main.add_metadata_to_cache')
    @patch('napps.kytos.storehouse.main.Box')
    def test_rest_create_201(self, *args):
        """Test rest_create method to HTTP 201 response."""
        (mock_box, mock_add_metadata_to_cache) = args
        box = MagicMock()
        box.box_id = '123'
        box.name = 'ABC'
        mock_box.return_value = box

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/namespace/123" % self.API_URL
        response = api.open(url, method='POST', json={'data': '123'})

        mock_add_metadata_to_cache.assert_called_with(box)
        self.napp.backend.create.assert_called_with(box)
        self.assertEqual(response.status_code, 201)

    def test_rest_create_400(self, *args):
        """Test rest_create method to HTTP 400 response."""
        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/namespace/123" % self.API_URL
        response = api.open(url, method='POST')

        self.assertEqual(response.status_code, 400)

    @patch('napps.kytos.storehouse.main.Main.add_metadata_to_cache')
    @patch('napps.kytos.storehouse.main.Box')
    def test_rest_create_v2_201(self, *args):
        """Test rest_create_v2 method to HTTP 201 response."""
        (mock_box, mock_add_metadata_to_cache) = args
        box = MagicMock()
        box.box_id = '123'
        box.name = 'ABC'
        mock_box.return_value = box

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v2/namespace/123" % self.API_URL
        response = api.open(url, method='POST', json={'data': '123'})

        mock_add_metadata_to_cache.assert_called_with(box)
        self.napp.backend.create.assert_called_with(box)
        self.assertEqual(response.status_code, 201)

    def test_rest_create_v2_400(self, *args):
        """Test rest_create_v2 method to HTTP 400 response."""
        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v2/namespace/123" % self.API_URL
        response = api.open(url, method='POST')

        self.assertEqual(response.status_code, 400)

    def test_rest_list(self):
        """Test rest_list method."""
        self.napp.backend.list.return_value = ['123', '456']

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/namespace" % self.API_URL
        response = api.open(url, method='GET')

        self.assertEqual(response.json, ['123', '456'])
        self.assertEqual(response.status_code, 200)

    def test_rest_update_200_patch(self):
        """Test rest_update method to HTTP 200 response with PATCH."""
        box = MagicMock()
        box.data = {'data': 'any'}
        self.napp.backend.retrieve.return_value = box

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/namespace/123" % self.API_URL
        response = api.open(url, method='PATCH', json={'data': '123'})

        self.napp.backend.update.assert_called_with('namespace', box)
        self.assertEqual(response.status_code, 200)

    def test_rest_update_200_put(self):
        """Test rest_update method to HTTP 200 response with PUT."""
        box = MagicMock()
        box.data = {'data': 'any'}
        self.napp.backend.retrieve.return_value = box

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/namespace/123" % self.API_URL
        response = api.open(url, method='PUT', json={'data': '123'})

        self.napp.backend.update.assert_called_with('namespace', box)
        self.assertEqual(response.status_code, 200)

    def test_rest_update_404(self):
        """Test rest_update method to HTTP 404 response."""
        self.napp.backend.retrieve.return_value = None

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/namespace/123" % self.API_URL
        response = api.open(url, method='PUT', json={'data': '123'})

        self.assertEqual(response.status_code, 404)

    def test_rest_update_400(self):
        """Test rest_update method to HTTP 400 response."""
        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/namespace/123" % self.API_URL
        response = api.open(url, method='PUT')

        self.assertEqual(response.status_code, 400)

    def test_rest_retrieve_200(self):
        """Test rest_retrieve method to HTTP 200 response."""
        box = MagicMock()
        box.data = {'data': 'any'}
        self.napp.backend.retrieve.return_value = box

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/namespace/123" % self.API_URL
        response = api.open(url, method='GET')

        self.napp.backend.retrieve.assert_called_with('namespace', '123')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'data': 'any'})

    def test_rest_retrieve_404(self):
        """Test rest_retrieve method to HTTP 404 response."""
        self.napp.backend.retrieve.return_value = None

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/namespace/123" % self.API_URL
        response = api.open(url, method='GET')

        self.assertEqual(response.status_code, 404)

    @patch('napps.kytos.storehouse.main.Main.delete_metadata_from_cache')
    def test_rest_delete_200(self, mock_delete_metadata):
        """Test rest_delete method to HTTP 200 response."""
        self.napp.backend.delete.return_value = True

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/namespace/123" % self.API_URL
        response = api.open(url, method='DELETE')

        mock_delete_metadata.assert_called_once_with('namespace', '123')
        self.napp.backend.delete.assert_called_with('namespace', '123')
        self.assertEqual(response.status_code, 200)

    @patch('napps.kytos.storehouse.main.Main.delete_metadata_from_cache')
    def test_rest_delete_404(self, mock_delete_metadata):
        """Test rest_delete method to HTTP 404 response."""
        self.napp.backend.delete.return_value = False

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/namespace/123" % self.API_URL
        response = api.open(url, method='DELETE')

        self.assertEqual(response.status_code, 404)

    @patch('napps.kytos.storehouse.main.Main.search_metadata_by')
    def test_rest_search_by_200(self, mock_search_metadata_by):
        """Test rest_search_by method to HTTP 200 response."""
        mock_search_metadata_by.return_value = {'box_id': '123'}

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/namespace/search_by/name/ABC" % self.API_URL
        response = api.open(url, method='GET')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'box_id': '123'})

    @patch('napps.kytos.storehouse.main.Main.search_metadata_by')
    def test_rest_search_by_404(self, mock_search_metadata_by):
        """Test rest_search_by method to HTTP 404 response."""
        mock_search_metadata_by.return_value = False

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/namespace/search_by/name/ABC" % self.API_URL
        response = api.open(url, method='GET')

        self.assertEqual(response.status_code, 404)

    def test_rest_backup_200(self):
        """Test rest_backup method to HTTP 200 response."""
        self.napp.backend.backup.return_value = 'backup'

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/backup/namespace/123" % self.API_URL
        response = api.open(url, method='GET')

        self.napp.backend.backup.assert_called_with('namespace', '123')
        self.assertEqual(response.status_code, 200)

    def test_rest_backup_404(self):
        """Test rest_backup method to HTTP 404 response."""
        self.napp.backend.backup.side_effect = [ValueError()]

        api = get_test_client(self.napp.controller, self.napp)
        url = "%s/v1/backup/namespace/123" % self.API_URL
        response = api.open(url, method='GET')

        self.assertEqual(response.status_code, 404)

    @patch('napps.kytos.storehouse.main.Box')
    @patch('napps.kytos.storehouse.main.Main._execute_callback')
    @patch('napps.kytos.storehouse.main.Main.add_metadata_to_cache')
    @patch('napps.kytos.storehouse.main.Main.search_metadata_by')
    def test_event_create_success_case(self, *args):
        """Test event_create method to success case."""
        (mock_search_metadata_by, mock_add_metadata_to_cache, _,
         mock_box) = args
        mock_search_metadata_by.return_value = False

        event = get_kytos_event_mock(name='kytos.storehouse.create',
                                     content={'namespace': 'namespace',
                                              'box_id': 'box_id',
                                              'data': 'data'})

        self.napp.event_create(event)

        self.napp.backend.create.assert_called_with(mock_box.return_value)
        mock_add_metadata_to_cache.assert_called_with(mock_box.return_value)

    @patch('napps.kytos.storehouse.main.Main._execute_callback')
    @patch('napps.kytos.storehouse.main.Main.add_metadata_to_cache')
    @patch('napps.kytos.storehouse.main.Main.search_metadata_by')
    def test_event_create_failure_case(self, *args):
        """Test event_create method to failure case."""
        (mock_search_metadata_by, mock_add_metadata_to_cache, _) = args
        mock_search_metadata_by.return_value = True

        event = get_kytos_event_mock(name='kytos.storehouse.create',
                                     content={'namespace': 'namespace',
                                              'box_id': '123',
                                              'data': 'data'})

        self.napp.event_create(event)

        self.napp.backend.create.assert_not_called()
        mock_add_metadata_to_cache.assert_not_called()

    @patch('napps.kytos.storehouse.main.Main._execute_callback')
    def test_event_retrieve_success_case(self, mock_execute_callback):
        """Test event_retrieve method to success case."""
        box = MagicMock()
        self.napp.backend.retrieve.return_value = box

        event = get_kytos_event_mock(name='kytos.storehouse.retrieve',
                                     content={'namespace': 'namespace',
                                              'box_id': '123'})

        self.napp.event_retrieve(event)

        self.napp.backend.retrieve.assert_called_with('namespace', '123')
        mock_execute_callback.assert_called_with(event, box, None)

    @patch('napps.kytos.storehouse.main.Main._execute_callback')
    def test_event_retrieve_failure_case(self, mock_execute_callback):
        """Test event_retrieve method to failure case."""
        error = KeyError()
        self.napp.backend.retrieve.side_effect = [error]

        event = get_kytos_event_mock(name='kytos.storehouse.retrieve',
                                     content={'namespace': 'namespace',
                                              'box_id': '123'})
        self.napp.event_retrieve(event)

        mock_execute_callback.assert_called_with(event, None, error)

    @patch('napps.kytos.storehouse.main.Main._execute_callback')
    def test_event_update_success_case(self, mock_execute_callback):
        """Test event_update method to success case."""
        box = MagicMock()
        self.napp.backend.retrieve.return_value = box

        event = get_kytos_event_mock(name='kytos.storehouse.update',
                                     content={'namespace': 'namespace',
                                              'box_id': '123'})
        self.napp.event_update(event)

        self.napp.backend.update.assert_called_with('namespace', box)

    @patch('napps.kytos.storehouse.main.Main._execute_callback')
    def test_event_update_failure_case(self, mock_execute_callback):
        """Test event_update method to failure case."""
        self.napp.backend.retrieve.return_value = None

        event = get_kytos_event_mock(name='kytos.storehouse.update',
                                     content={'namespace': 'namespace',
                                              'box_id': '123'})
        self.napp.event_update(event)

        self.napp.backend.update.assert_not_called()

    @patch('napps.kytos.storehouse.main.Main._execute_callback')
    @patch('napps.kytos.storehouse.main.Main.delete_metadata_from_cache')
    def test_event_delete_success_case(self, *args):
        """Test event_delete method to success case."""
        (mock_delete_metadata, _) = args
        self.napp.backend.delete.return_value = 'result'

        event = get_kytos_event_mock(name='kytos.storehouse.delete',
                                     content={'namespace': 'namespace',
                                              'box_id': '123'})

        self.napp.event_delete(event)

        self.napp.backend.delete.assert_called_once_with('namespace', '123')
        mock_delete_metadata.assert_called_once_with('namespace', '123')

    @patch('napps.kytos.storehouse.main.Main._execute_callback')
    @patch('napps.kytos.storehouse.main.Main.delete_metadata_from_cache')
    def test_event_delete_failure_case(self, *args):
        """Test event_delete method to failure case."""
        (mock_delete_metadata, _) = args
        event = get_kytos_event_mock(name='kytos.storehouse.delete',
                                     content={})

        self.napp.event_delete(event)

        self.napp.backend.delete.assert_not_called()
        mock_delete_metadata.assert_not_called()

    @patch('napps.kytos.storehouse.main.Main._execute_callback')
    def test_event_list_success_case(self, mock_execute_callback):
        """Test event_list method to success case."""
        result = MagicMock()
        self.napp.backend.list.return_value = result

        event = get_kytos_event_mock(name='kytos.storehouse.list',
                                     content={'namespace': 'namespace'})
        self.napp.event_list(event)

        mock_execute_callback.assert_called_with(event, result, None)

    @patch('napps.kytos.storehouse.main.Main._execute_callback')
    def test_event_list_failure_case(self, mock_execute_callback):
        """Test event_list method to failure case."""
        error = KeyError()
        self.napp.backend.list.side_effect = [error]

        event = get_kytos_event_mock(name='kytos.storehouse.list',
                                     content={'namespace': 'namespace'})
        self.napp.event_list(event)

        mock_execute_callback.assert_called_with(event, None, error)
