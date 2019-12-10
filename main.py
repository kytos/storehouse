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


def metadata_from_box(box):
    """Return a metadata from box."""
    return {"box_id": box.box_id,
            "name": box.name,
            "owner": box.owner,
            "created_at": box.created_at}


class Box:
    """Store data with the necessary metadata."""

    def __init__(self, data, namespace, name=None, box_id=None):
        """Create a new Box instance.

        Args:
            data: Data to be stored in the box.
            namespace: Namespace where the box belongs.

        """
        self.data = data
        self.namespace = namespace
        self.name = name
        if box_id is None:
            box_id = uuid4().hex
        self.box_id = box_id
        self.created_at = str(datetime.utcnow())
        self.owner = None

    def __str__(self):
        return '%s.%s' % (self.namespace, self.box_id)

    @property
    def name(self):
        """Return name from Box instance.

        Returns:
            string: Box name.

        """
        log.warning("The name parameter will be deprecated soon.")
        return self._name

    @name.setter
    def name(self, value):
        log.warning("The name parameter will be deprecated soon.")
        self._name = value  # pylint: disable=attribute-defined-outside-init

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
        if settings.BACKEND == "etcd":
            from napps.kytos.storehouse.backends.etcd import Etcd
            log.info("Loading 'etcd' backend...")
            self.backend = Etcd()
        else:
            from napps.kytos.storehouse.backends.fs import FileSystem
            log.info("Loading 'filesystem' backend...")
            self.backend = FileSystem()

        self.metadata_cache = {}
        self.create_cache()
        log.info("Storehouse NApp started.")

    def execute(self):
        """Execute after the setup method."""

    def create_cache(self):
        """Create a cache from all namespaces when the napp setup."""
        log.debug('Creating storehouse cache...')
        for namespace in self.backend.list_namespaces():
            if namespace not in self.metadata_cache:
                self.metadata_cache[namespace] = []

            for box_id in self.backend.list(namespace):
                box = self.backend.retrieve(namespace, box_id)
                log.debug("Loading box '%s'...", box)
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
            if (box_id and box_id in cache["box_id"] or
                    name and name in cache["name"]):
                self.metadata_cache.get(namespace, []).remove(cache)

    def add_metadata_to_cache(self, box):
        """Add a box cache into the namespace cache."""
        cache = metadata_from_box(box)
        if box.namespace not in self.metadata_cache:
            self.metadata_cache[box.namespace] = []
        self.metadata_cache[box.namespace].append(cache)

    def search_metadata_by(self, namespace, filter_option="box_id", query=""):
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
        self.backend.create(box)
        self.add_metadata_to_cache(box)

        result = {"response": "Box created.", "id": box.box_id}

        if name:
            result["name"] = box.name

        return jsonify(result), 201

    @rest('v2/<namespace>', methods=['POST'])
    @rest('v2/<namespace>/<box_id>', methods=['POST'])
    def rest_create(self, namespace, box_id=None):
        """Create a box in a namespace based on JSON input."""
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"response": "Invalid Request"}), 500

        box = Box(data, namespace, box_id=box_id)
        self.backend.create(box)
        self.add_metadata_to_cache(box)

        result = {"response": "Box created.", "id": box.box_id}

        return jsonify(result), 201

    @rest('v1/<namespace>', methods=['GET'])
    def rest_list(self, namespace):
        """List all boxes in a namespace."""
        result = self.backend.list(namespace)
        return jsonify(result), 200

    @rest('v1/<namespace>/<box_id>', methods=['PUT', 'PATCH'])
    def rest_update(self, namespace, box_id):
        """Update a box_id from namespace."""
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"response": "Invalid request: empty data"}), 500

        box = self.backend.retrieve(namespace, box_id)

        if not box:
            return jsonify({"response": "Not Found"}), 404

        if request.method == "PUT":
            box.data = data
        else:
            box.data.update(data)

        self.backend.update(namespace, box)

        return jsonify(box.data), 200

    @rest('v1/<namespace>/<box_id>', methods=['GET'])
    def rest_retrieve(self, namespace, box_id):
        """Retrieve and return a box from a namespace."""
        box = self.backend.retrieve(namespace, box_id)

        if not box:
            return jsonify({"response": "Not Found"}), 404

        return jsonify(box.data), 200

    @rest('v1/<namespace>/<box_id>', methods=['DELETE'])
    def rest_delete(self, namespace, box_id):
        """Delete a box from a namespace."""
        result = self.backend.delete(namespace, box_id)

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
        error = None
        box_id = event.content.get('box_id')

        try:
            data = event.content['data']
            namespace = event.content['namespace']

            if self.search_metadata_by(namespace, query=box_id):
                raise KeyError("Box id already exists.")

        except KeyError as exc:
            box = None
            error = exc
        else:
            box = Box(data, namespace, box_id=box_id)
            self.backend.create(box)
            self.add_metadata_to_cache(box)

        self._execute_callback(event, box, error)

    @listen_to('kytos.storehouse.retrieve')
    def event_retrieve(self, event):
        """Retrieve a box from a namespace based on an event."""
        error = None

        try:
            box = self.backend.retrieve(event.content['namespace'],
                                        event.content['box_id'])
        except KeyError as exc:
            box = None
            error = exc

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

        try:
            namespace = event.content['namespace']
            box_id = event.content['box_id']
            box = self.backend.retrieve(namespace, box_id)
            if not box:
                raise KeyError("Box id does not exist.")

        except KeyError as exc:
            box = None
            error = exc
        else:
            method = event.content.get('method', 'PATCH')
            data = event.content.get('data', {})

            if method == 'PUT':
                box.data = data
            elif method == 'PATCH':
                box.data.update(data)

            self.backend.update(namespace, box)

        self._execute_callback(event, box, error)

    @listen_to('kytos.storehouse.delete')
    def event_delete(self, event):
        """Delete a box from a namespace based on an event."""
        error = None

        try:
            namespace = event.content['namespace']
            box_id = event.content['box_id']
        except KeyError as exc:
            result = None
            error = exc
        else:
            result = self.backend.delete(namespace, box_id)
            self.delete_metadata_from_cache(namespace, box_id)

        self._execute_callback(event, result, error)

    @listen_to('kytos.storehouse.list')
    def event_list(self, event):
        """List all boxes in a namespace based on an event."""
        error = None

        try:
            result = self.backend.list(event.content['namespace'])

        except KeyError as exc:
            result = None
            error = exc

        self._execute_callback(event, result, error)

    @rest("v1/backup/<namespace>/", methods=['GET'])
    @rest("v1/backup/<namespace>/<box_id>", methods=['GET'])
    def rest_backup(self, namespace, box_id=None):
        """Backup an entire namespace or an object based on its id."""
        try:
            return jsonify(self.backend.backup(namespace, box_id)), 200
        except ValueError:
            return jsonify({"response": "Not Found"}), 404

    def shutdown(self):
        """Execute before the NApp is unloaded."""
        log.info("Storehouse NApp is shutting down.")
