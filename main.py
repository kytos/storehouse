"""Main module of kytos/storehouse Kytos Network Application.

Persistence NApp with support for multiple backends.
"""

import json
import re
from datetime import datetime
from uuid import uuid4

from flask import jsonify, request
from kytos.core import KytosNApp, log, rest
from kytos.core.helpers import listen_to

from napps.kytos.storehouse import settings  # pylint: disable=unused-import
from napps.kytos.storehouse.backends.fs import FileSystem


def metadata_from_box(box):
    """Return a metadata from box."""
    return {"box_id": box.box_id,
            "name": box.name,
            "owner": box.owner,
            "created_at": box.created_at}


class Box:
    """Store data with the necessary metadata."""

    def __init__(self, data, namespace, name=None):
        """Create a new Box instance.

        Args:
            data: Data to be stored in the box.
            namespace: Namespace where the box belongs.

        """
        self.data = data
        self.namespace = namespace
        self.name = name
        self.box_id = uuid4().hex
        self.created_at = str(datetime.utcnow())
        self.owner = None

    @property
    def name(self):
        log.warning("The name parameter will be deprecated soon.")
        return self._name

    @name.setter
    def name(self, value):
        log.warning("The name parameter will be deprecated soon.")
        self._name = value

    @classmethod
    def from_json(cls, json_data):
        """Create a new Box instance from JSON input."""
        raw = json.loads(json_data)
        data = raw.get('data')
        namespace = raw.get('namespace')
        name = raw.get('name')
        return cls(data, namespace, name)

    def to_dict(self):
        """Return the instance as a python dictionary."""
        return {'data': self.data,
                'namespace': self.namespace,
                'owner': self.owner,
                'created_at': self.created_at,
                'id': self.box_id,
                'name': self.name}

    def to_json(self):
        """Return the instance as a JSON string."""
        return json.dumps(self.to_dict(), indent=4)


class Main(KytosNApp):
    """Main class of kytos/storehouse NApp.

    This class is the entry point for this napp.
    """

    metadata_cache = {}

    def setup(self):
        """Replace the '__init__' method for the KytosNApp subclass.

        Execute right after the NApp is loaded.
        """
        self.metadata_cache = {}
        self.create_cache()
        log.info("Storehouse NApp started.")

    def execute(self):
        """Execute after the setup method."""

    def create_cache(self):
        """Create a cache from all namespaces when the napp setup."""
        backend = FileSystem()
        for namespace in backend.list_namespaces():
            if namespace not in self.metadata_cache:
                self.metadata_cache[namespace] = []

            for box_id in backend.list(namespace):
                box = backend.retrieve(namespace, box_id)
                cache = metadata_from_box(box)
                self.metadata_cache[namespace].append(cache)

    def delete_metadata_from_cache(self, namespace, box_id=None, name=None):
        """Delete a metadata from cache.

        Args:
            namespace(str): A namespace, when the box will be deleted
            box_id(str): Box identifier
            name(str):  Box name

        """
        for cache in self.metadata_cache.get(namespace, []):
            if box_id in cache["box_id"] or name in cache["name"]:
                self.metadata_cache.get(namespace, []).remove(cache)

    def add_metadata_to_cache(self, box):
        """Add a box cache into the namespace cache."""
        cache = metadata_from_box(box)
        if box.namespace not in self.metadata_cache:
            self.metadata_cache[box.namespace] = []
        self.metadata_cache[box.namespace].append(cache)

    def search_metadata_by(self, namespace, filter_option="id", query=""):
        """Search for all metadata with specific pattern.

        Args:
            namespace(str): namespace where the box is stored
            filter_option(str): metadata option
            query(str): query to be searched

        Returns:
            list: list of metadata box filtered

        """
        namespace_cache = self.metadata_cache.get(namespace, [])
        results = []

        for metadata in namespace_cache:
            field_value = metadata.get(filter_option, "")
            if re.match(f".*{query}.*", field_value):
                results.append(metadata)

        return results

    @staticmethod
    def _execute_callback(event, data, error):
        """Run the callback function for event calls to the NApp."""
        try:
            event.content['callback'](event, data, error)
        except KeyError:
            log.error(f'Event {event!r} without callback function!')
        except TypeError as exception:
            log.error(f"Bad callback function {event.content['callback']}!")
            log.error(exception)

    @rest('v1/<namespace>', methods=['POST'])
    @rest('v1/<namespace>/<name>', methods=['POST'])
    def rest_create(self, namespace, name=None):
        """Create a box in a namespace based on JSON input."""
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"response": "Invalid Request"}), 500

        box = Box(data, namespace, name)
        backend = FileSystem()
        backend.create(box)
        self.add_metadata_to_cache(box)

        result = {"response": "Box created.", "id": box.box_id}

        if name:
            result["name"] = box.name

        return jsonify(result), 201

    @staticmethod
    @rest('v1/<namespace>', methods=['GET'])
    def rest_list(namespace):
        """List all boxes in a namespace."""
        backend = FileSystem()
        result = backend.list(namespace)
        return jsonify(result), 200

    @staticmethod
    @rest('v1/<namespace>/<box_id>', methods=['PUT', 'PATCH'])
    def rest_update(namespace, box_id):
        """Update a box_id from namespace."""
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"response": "Invalid request: empty data"}), 500

        backend = FileSystem()
        box = backend.retrieve(namespace, box_id)

        if not box:
            return jsonify({"response": "Not Found"}), 404

        if request.method == "PUT":
            box.data = data
        else:
            box.data.update(data)

        backend.update(namespace, box)

        return jsonify(box.data), 200

    @staticmethod
    @rest('v1/<namespace>/<box_id>', methods=['GET'])
    def rest_retrieve(namespace, box_id):
        """Retrieve and return a box from a namespace."""
        backend = FileSystem()
        box = backend.retrieve(namespace, box_id)

        if not box:
            return jsonify({"response": "Not Found"}), 404

        return jsonify(box.data), 200

    @rest('v1/<namespace>/<box_id>', methods=['DELETE'])
    def rest_delete(self, namespace, box_id):
        """Delete a box from a namespace."""
        backend = FileSystem()
        result = backend.delete(namespace, box_id)

        if result:
            self.delete_metadata_from_cache(namespace, box_id)
            return jsonify({"response": "Box deleted"}), 202

        return jsonify({"response": "Unable to complete request"}), 500

    @rest("v1/<namespace>/search_by/<filter_option>/<query>", methods=['GET'])
    def rest_search_by(self, namespace, filter_option="name", query=""):
        """Filter the boxes with specific pattern.

        Args:
            namespace(str): namespace where the box is stored
            filter_option(str): metadata option
            query(str): query to be searched

        Returns:
            list: list of metadata box filtered

        """
        results = self.search_metadata_by(namespace, filter_option, query)

        if not results:
            return jsonify({"response": f"{filter_option} not found"}), 404

        return jsonify(results), 200

    @listen_to('kytos.storehouse.create')
    def event_create(self, event):
        """Create a box in a namespace based on an event."""
        error = False

        try:
            box = Box(event.content['data'], event.content['namespace'])
            backend = FileSystem()
            backend.create(box)
            self.add_metadata_to_cache(box)
        except KeyError:
            box = None
            error = True

        self._execute_callback(event, box, error)

    @listen_to('kytos.storehouse.retrieve')
    def event_retrieve(self, event):
        """Retrieve a box from a namespace based on an event."""
        error = False

        try:
            backend = FileSystem()
            box = backend.retrieve(event.content['namespace'],
                                   event.content['box_id'])
        except KeyError:
            box = None
            error = True

        self._execute_callback(event, box, error)

    @listen_to('kytos.storehouse.update')
    def event_update(self, event):
        """Update a box_id from namespace.

        This method receive an KytosEvent with the content bellow.

        namespace: namespace where the box is stored
        box_id: the box identify
        method: 'PUT' or 'PATCH', the default update method is 'PATCH'
        data: a python dict with the data
        """
        error = False
        backend = FileSystem()

        try:
            namespace = event.content['namespace']
            box_id = event.content['box_id']
        except KeyError:
            box = None
            error = True

        box = backend.retrieve(namespace, box_id)
        method = event.content.get('method', 'PATCH')
        data = event.content.get('data', {})

        if box:
            if method == 'PUT':
                box.data = data
            elif method == 'PATCH':
                box.data.update(data)

            backend.update(namespace, box)

        self._execute_callback(event, box, error)

    @listen_to('kytos.storehouse.delete')
    def event_delete(self, event):
        """Delete a box from a namespace based on an event."""
        error = False
        backend = FileSystem()

        try:
            namespace = event.content['namespace']
            box_id = event.content['box_id']
            result = backend.delete(namespace, box_id)
            self.delete_metadata_from_cache(namespace, box_id)
        except KeyError:
            result = None
            error = True

        self._execute_callback(event, result, error)

    @listen_to('kytos.storehouse.list')
    def event_list(self, event):
        """List all boxes in a namespace based on an event."""
        error = False
        backend = FileSystem()

        try:
            result = backend.list(event.content['namespace'])

        except KeyError:
            result = None
            error = True

        self._execute_callback(event, result, error)

    @rest("v1/backup/<namespace>/", methods=['GET'])
    @rest("v1/backup/<namespace>/<box_id>", methods=['GET'])
    @staticmethod
    def rest_backup(namespace, box_id=None):
        """Backup an entire namespace or an object based on its id."""
        backend = FileSystem()
        try:
            return jsonify(backend.backup(namespace, box_id)), 200
        except ValueError:
            return jsonify({"response": "Not Found"}), 404

    def shutdown(self):
        """Execute before the NApp is unloaded."""
        log.info("Storehouse NApp is shutting down.")
