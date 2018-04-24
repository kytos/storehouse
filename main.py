"""Main module of kytos/storehouse Kytos Network Application.

Persistence NApp with support to multiple backends.
"""

import json
from datetime import datetime
from uuid import uuid4

from flask import jsonify, request

from kytos.core import KytosNApp, log, rest
from kytos.core.helpers import listen_to
from napps.kytos.storehouse import settings  # pylint: disable=unused-import
from napps.kytos.storehouse.backends.fs import FileSystem


class Box:
    """Store data with the necesary metadata."""

    def __init__(self, data, namespace):
        """Create a new Box instance.

        Args:
            data: Data to be stored in the box.
            namespace: Namespace where the box belongs.
        """
        self.data = data
        self.namespace = namespace
        self.box_id = uuid4().hex
        self.created_at = str(datetime.utcnow())
        self.owner = None

    @classmethod
    def from_json(cls, json_data):
        """Create new instance from input JSON."""
        raw = json.loads(json_data)
        data = raw['data']
        namespace = raw['namespace']
        return cls(data, namespace)

    def to_dict(self):
        """Return the instance as a python dictionary."""
        return {'data': self.data,
                'namespace': self.namespace,
                'owner': self.owner,
                'created_at': self.created_at,
                'id': self.box_id}

    def to_json(self):
        """Return the instance as a JSON string."""
        return json.dumps(self.to_dict(), indent=4)


class Main(KytosNApp):
    """Main class of kytos/storehouse NApp.

    This class is the entry point for this napp.
    """

    def setup(self):
        """Replace the '__init__' method for the KytosNApp subclass.

        Execute right after the NApp is loaded.
        """
        log.info("Storehouse NApp started.")

    def execute(self):
        """Execute after the setup method."""
        pass

    @staticmethod
    def _execute_callback(event, data, error):
        """Run the callback function for event calls to the NApp."""
        try:
            event.content['callback'](data, error)
        except KeyError:
            log.error('Create: event without callback function!')
        except TypeError as exception:
            log.error('Create: bad callback function!')
            log.error(exception)

    @staticmethod
    @rest('v1/<namespace>', methods=['POST'])
    def rest_create(namespace):
        """Create a box in a namespace based on JSON input."""
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"response": "Invalid Request"}), 500

        box = Box(data, namespace)
        backend = FileSystem()
        backend.create(box)
        return jsonify({"response": "Box created.",
                        "id": box.box_id}), 201

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
            return jsonify({"response": "Invalid Request"}), 500

        backend= FileSystem()
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

    @staticmethod
    @rest('v1/<namespace>/<box_id>', methods=['DELETE'])
    def rest_delete(namespace, box_id):
        """Delete a box from a namespace."""
        backend = FileSystem()
        result = backend.delete(namespace, box_id)
        if result:
            return jsonify({"response": "Box deleted"}), 202

        return jsonify({"response": "Unable to complete request"}), 500

    @listen_to('kytos.storehouse.create')
    def event_create(self, event):
        """Create a box in a namespace based on an event."""
        error = False

        try:
            box = Box(event.content['data'], event.content['namespace'])
            backend = FileSystem()
            backend.create(box)

        except (AttributeError, KeyError, TypeError, ValueError):
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

        except (AttributeError, KeyError, TypeError, ValueError):
            box = None
            error = True

        self._execute_callback(event, box, error)

    @listen_to('kytos.storehouse.update')
    def event_update(self, event):
        """Update a box_id from namespace.

        This method receive an event with the follow parameters:

        namespace: namespace where the box is stored
        box_id: the box identify
        method: 'PUT' or 'PATCH', the default update method is 'PATCH'
        data: a python dict with the data
        """
        error = False

        try:
            backend = FileSystem()
            box = backend.retrieve(event.content['namespace'],
                                   event.content['box_id'])
        except (AttributeError, KeyError, TypeError, ValueError):
            box = None
            error = True

        method = event.content.get('method', 'PATCH')
        data =  event.content.get('data', {})

        if box:
            if method == 'PUT':
                box.data = data
            else:
                box.data.update(data)

            backend.update(namespace, box)

        self._execute_callback(event, box, error)

    @listen_to('kytos.storehouse.delete')
    def event_delete(self, event):
        """Delete a box from a namespace based on an event."""
        error = False

        try:
            backend = FileSystem()
            result = backend.delete(event.content['namespace'],
                                    event.content['box_id'])

        except (AttributeError, KeyError, TypeError, ValueError):
            result = None
            error = True

        self._execute_callback(event, result, error)

    @listen_to('kytos.storehouse.list')
    def event_list(self, event):
        """List all boxes in a namespace based on an event."""
        error = False

        try:
            backend = FileSystem()
            result = backend.list(event.content['namespace'])

        except (AttributeError, KeyError, TypeError, ValueError):
            result = None
            error = True

        self._execute_callback(event, result, error)

    def shutdown(self):
        """Execute before tha NApp is unloaded."""
        log.info("Storehouse NApp is shutting down.")
