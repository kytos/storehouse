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

    @staticmethod
    @listen_to('kytos.storehouse.create')
    def event_create(event):
        """Create a box in a namespace based on an event."""
        box = Box(event.content['data'], event.content['namespace'])
        backend = FileSystem()
        backend.create(box)

        try:
            event.content['callback'](box, error=False)
        except KeyError:
            log.error('Create: event without callback function!')
        except TypeError as error:
            log.error('Create: bad callback function!')
            log.error(e)

    @staticmethod
    @listen_to('kytos.storehouse.retrieve')
    def event_retrieve(event):
        """Retrieve a box from a namespace based on an event."""
        backend = FileSystem()
        box = backend.retrieve(event.content['namespace'],
                               event.content['box_id'])

        try:
            event.content['callback'](box, error=False)
        except KeyError:
            log.error('Retrieve: event without callback function!')
        except TypeError:
            log.error('Retrieve: bad callback function!')
            log.error(e)

    @staticmethod
    @listen_to('kytos.storehouse.delete')
    def event_delete(event):
        """Delete a box from a namespace based on an event."""
        backend = FileSystem()
        result = backend.delete(event.content['namespace'],
                                event.content['box_id'])

        try:
            event.content['callback'](result, error=False)
        except KeyError:
            log.error('Delete: event without callback function!')
        except TypeError:
            log.error('Delete: bad callback function!')
            log.error(e)

    @staticmethod
    @listen_to('kytos.storehouse.list')
    def event_list(event):
        """List all boxes in a namespace based on an event."""
        backend = FileSystem()
        result = backend.list(event.content['namespace'])

        try:
            event.content['callback'](result, error=False)
        except KeyError:
            log.error('List: event without callback function!')
        except TypeError:
            log.error('List: bad callback function!')
            log.error(e)

    def shutdown(self):
        """Execute before tha NApp is unloaded."""
        log.info("Storehouse NApp is shutting down.")
