"""Main module of kytos/storehouse Kytos Network Application.

Persistence NApp with support to multiple backends
"""

from kytos.core import KytosNApp, log, rest
from napps.kytos.storehouse import settings
from napps.kytos.storehouse.backends.fs import FileSystem

from flask import jsonify, request
from uuid import uuid4
from datetime import datetime

import json

class Box:
    def __init__(self, data, namespace):
        self.data = data
        self.namespace = namespace
        self.id = uuid4().hex
        self.created_at = str(datetime.utcnow())
        self.owner = None # TODO: implement permissions

    @classmethod
    def from_json(cls, json_data):
        raw = json.loads(json_data)
        data = raw['data']
        namespace = raw['data']
        return cls(data, namespace)

    def as_dict(self):
        return  {'data': self.data,
                 'namespace': self.namespace,
                 'owner': self.owner,
                 'created_at': self.created_at,
                 'id': self.id}

    def as_json(self):
        return json.dumps(self.as_dict(), indent=4)


class Main(KytosNApp):
    """Main class of kytos/storehouse NApp.

    This class is the entry point for this napp.
    """

    def setup(self):
        """Replace the '__init__' method for the KytosNApp subclass.

        The setup method is automatically called by the controller when your
        application is loaded.

        So, if you have any setup routine, insert it here.
        """
        pass

    def execute(self):
        """This method is executed right after the setup method execution.

        You can also use this method in loop mode if you add to the above setup
        method a line like the following example:

            self.execute_as_loop(30)  # 30-second interval.
        """
        pass

    @rest('v1/<namespace>', methods=['POST'])
    def create(self, namespace):
        """Create a box based on a data."""
        data = request.get_json(silent=True)
        if not data:
            return json.dumps({"response": "Invalid Request"}), 500

        box = Box(data, namespace)
        # TODO: For now, we have only fs, but we must change this to support
        # multiple backends
        backend = FileSystem()
        backend.create(box)
        return json.dumps({"response": "Box created.",
                           "id": box.id}), 201

    @rest('v1/<namespace>', methods=['GET'])
    def list(self, namespace):
        backend = FileSystem()
        result = backend.list(namespace)
        return json.dumps(result), 200

    @rest('v1/<namespace>/<box_id>', methods=['GET'])
    def retrieve(self, namespace, box_id):
        backend = FileSystem()
        box = backend.retrieve(namespace, box_id)
        if not box:
            return json.dumps({"response": "Not Found"}), 404

        return json.dumps(box.data), 200

    @rest('v1/<namespace>/<box_id>', methods=['DELETE'])
    def delete(self, namespace, box_id):
        backend = FileSystem()
        result = backend.delete(namespace, box_id)
        if result:
            return json.dumps({"response": "Box deletedd"}), 202
        else:
            return json.dumps({"response": "Unable to complete request"}), 500

    def shutdown(self):
        """This method is executed when your napp is unloaded.

        If you have some cleanup procedure, insert it here.
        """
        pass
