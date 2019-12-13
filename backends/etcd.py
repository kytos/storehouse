"""etcd backend for storehouse."""

import pickle
from typing import Union

import etcd3

from napps.kytos.storehouse.backends.base import StoreBase


def split_fullname(fullname: bytes):
    """
    Split full backend string name into (namespace, box_id) tuple.

    >>> split_fullname(b'name.space.box_id')
    [b'name.space', b'box_id']
    """
    return fullname.rsplit(b'.', maxsplit=1)


def join_fullname(namespace: Union[bytes, str], box_id: Union[bytes, str]):
    """Join (namespace, box_id) tuple into a "namespace.box_id" string."""
    if isinstance(namespace, bytes) and isinstance(box_id, bytes):
        return namespace + b'.' + box_id
    return f'{namespace}.{box_id}'


class Etcd(StoreBase):
    """etcd client."""

    def __init__(self):
        self.etcd = etcd3.client()

    def _get_all_keys(self):
        return (r[1].key for r in self.etcd.get_all(keys_only=True))

    def create(self, box):
        """Create a new box."""
        raw_data = pickle.dumps(box)
        return self.etcd.put(join_fullname(box.namespace, box.box_id),
                             raw_data)

    def retrieve(self, namespace, box_id):
        """Retrieve a box from a namespace."""
        raw_data, _ = self.etcd.get(join_fullname(namespace, box_id))
        return pickle.loads(raw_data) if raw_data else raw_data

    def delete(self, namespace, box_id):
        """Delete a box from a namespace."""
        return self.etcd.delete(join_fullname(namespace, box_id))

    def list(self, namespace):
        """List all the box_id's in a namespace."""
        result = self.etcd.get_prefix(namespace, keys_only=True)
        return (split_fullname(obj.key)[1] for (_, obj) in result)

    def list_namespaces(self):
        """List all the namespaces registered."""
        return set(split_fullname(k)[0] for k in self._get_all_keys())

    def backup(self, namespace=None, box_id=None):
        """Backup all the namespaces registered."""
        return (pickle.loads(box) for box in self.etcd.get_all())

    get = retrieve
