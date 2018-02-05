"""FileSystem Backend for the Storehouse NApp.

Save and load data from the local filesystem.
"""

import pickle
from pathlib import Path

from napps.kytos.storehouse.backends.base import StoreBase

DESTINATION_PATH = "/tmp/kytos/storehouse"


class FileSystem(StoreBase):
    """Backend class for dealing with FileSystem operation.

    Save and load data from the local filesystem.
    """

    @staticmethod
    def _create_dirs(destination):
        Path(destination).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _get_destination(namespace):
        return Path(DESTINATION_PATH, namespace)

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
        if not destination.exists():
            return False

        return self._load_from_file(destination)

    def delete(self, namespace, box_id):
        """Delete a box from a namespace."""
        destination = self._get_destination(namespace).joinpath(box_id)

        return self._delete_file(destination) is None

    def list(self, namespace):
        """List all the boxes in a namespace."""
        return self._list_namespace(namespace)
