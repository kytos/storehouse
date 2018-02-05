"""FileSystem Backend for the Storehouse NApp.

Save and load data from the local filesystem.
"""

from napps.kytos.storehouse.backends.base import StoreBase
from pathlib import Path

import pickle

DESTINATION_PATH="/tmp/kytos/storehouse"


class FileSystem(StoreBase):
    """Backend class for dealing with FileSystem operation.

    Save and load data from the local filesystem.
    """

    def _create_dirs(self, destination):
        Path(destination).mkdir(parents=True, exist_ok=True)

    def _get_destination(self, namespace):
        return Path(DESTINATION_PATH, namespace)

    def _write_to_file(self, filename, box):
        with open(filename, 'wb') as fp:
            pickle.dump(box, fp)

    def _load_from_file(self, filename):
        try:
            with open(filename, 'rb') as fp:
                data = pickle.load(fp)
            return data
        except Exception: # TODO: specific exceptions here
            return False

    def _delete_file(self, path):
        if path.exists():
            return path.unlink()
        else:
            return False

    def _list_namespace(self, namespace):
        path = self._get_destination(namespace)
        if path.exists():
            return [x.name for x in path.iterdir() if not x.is_dir()]
        else:
            return []

    def create(self, box):
        """Create a new box."""
        destination = self._get_destination(box.namespace)
        self._create_dirs(destination)
        self._write_to_file(destination.joinpath(box.id), box)
        return box.id

    def retrieve(self, namespace, box_id):
        """Retrieve a box from a namespace."""
        destination = self._get_destination(namespace).joinpath(box_id)
        if not destination.exists():
            return False

        return self._load_from_file(destination)

    def delete(self, namespace, box_id):
        """Delete a box from a namespace."""
        destination = self._get_destination(namespace).joinpath(box_id)
        if self._delete_file(destination) is None:
            return True
        else:
            return False

    def list(self, namespace):
        """List all the boxes in a namespace."""
        return self._list_namespace(namespace)
