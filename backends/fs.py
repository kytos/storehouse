"""FileSystem Backend for the Storehouse NApp.

Save and load data from the local filesystem.
"""

import os
import pickle
from pathlib import Path

from filelock import FileLock
from kytos.core import log

from napps.kytos.storehouse import settings
from napps.kytos.storehouse.backends.base import StoreBase


class NotFoundException(Exception):
    """ NotFound Excpetion Class"""


class FileSystem(StoreBase):
    """Backend class for dealing with FileSystem operation.

    Save and load data from the local filesystem.
    """

    def __init__(self):
        """Constructor of FileSystem."""
        self.destination_path = settings.CUSTOM_DESTINATION_PATH
        self._parse_settings()

    @staticmethod
    def _create_dirs(destination):
        """Create directories given a destination."""
        Path(destination).mkdir(parents=True, exist_ok=True)

    def _parse_settings(self):
        """Parse settings.

        Update self.destination_path to use the specified path. If
        kytos is running in a virtualenv, the destination_path
        will be joined to the root of virtualenv path.
        """
        base_env = os.environ.get('VIRTUAL_ENV', None) or '/'
        if self.destination_path.startswith(os.path.sep):
            self.destination_path = self.destination_path[1:]
        self.destination_path = Path(base_env).joinpath(self.destination_path)
        self._create_dirs(self.destination_path)
        log.debug(f"FileSystem destination_path: {self.destination_path}")

    def _get_destination(self, namespace):
        """Get the destination path in this workspace."""
        return Path(self.destination_path, namespace)

    @staticmethod
    def _write_to_file(filename, box):
        with open(filename, 'wb') as save_file:
            pickle.dump(box, save_file)

    @staticmethod
    def _load_from_file(filename):
        try:
            with open(filename, 'rb') as load_file:
                data = pickle.load(load_file)
            return data
        except pickle.PickleError:
            return False

    @staticmethod
    def _delete_file(path):
        if path.exists():
            return path.unlink()

        return False

    def _list_namespace(self, namespace):
        path = self._get_destination(namespace)
        if path.exists():
            return [x.name for x in path.iterdir() if not x.is_dir()]

        return []

    def create(self, box):
        """Create a new box."""
        destination = self._get_destination(box.namespace)
        self._create_dirs(destination)
        self._write_to_file(destination.joinpath(box.box_id), box)
        return box.box_id

    def retrieve(self, namespace, box_id):
        """Retrieve a box from a namespace."""
        destination = self._get_destination(namespace).joinpath(box_id)
        if not destination.is_file():
            return False

        return self._load_from_file(destination)

    def update(self, namespace, box):
        """Update a box from a namespace."""
        destination = self._get_destination(namespace)
        self._write_to_file(destination.joinpath(box.box_id), box)
        return box.box_id

    def delete(self, namespace, box_id):
        """Delete a box from a namespace."""
        destination = self._get_destination(namespace).joinpath(box_id)

        return self._delete_file(destination) is None

    def list(self, namespace):
        """List all the boxes in a namespace."""
        return self._list_namespace(namespace)

    def list_namespaces(self):
        """List all the namespaces registered."""
        path = self._get_destination('.')
        if path.exists():
            return [x.name for x in path.iterdir() if x.is_dir()]
        return []

    def backup(self, namespace, box_id=None):
        """Make a dump of all boxes on a Namespace in a JSON format.

        If box_id is empty, then this method will return all boxes from the
        namespace.
        """
        if namespace not in self.list_namespaces():
            raise NotFoundException("Namespace not found")

        if box_id is None:
            boxes = self.list(namespace)
        else:
            boxes = [box_id]

        return {box: self.retrieve(namespace, box).to_json() for box in boxes}
