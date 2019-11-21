"""etcd backend for storehouse."""

import etcd3

from napps.kytos.storehouse.backends.base import StoreBase


class Etcd(StoreBase):
    """etcd client."""

    def __init__(self):
        self.etcd = etcd3.client()

    def create(self, box):
        """Create a new box."""
        return self.etcd.put(f'{box.namespace}.{box.box_id}', f'{box.data}')

    def retrieve(self, namespace, box_id):
        """Retrieve a box from a namespace."""
        return self.etcd.get(f'{namespace}.{box_id}')

    def delete(self, namespace, box_id):
        """Delete a box from a namespace."""
        return self.etcd.delete(f'{namespace}.{box_id}')

    def list(self, namespace):
        """List all the boxes in a namespace."""
        return self.etcd.get_prefix(namespace)

    def list_namespaces(self):
        """List all the namespaces registered."""
        return self.etcd.get_all(keys_only=True)

    def backup(self, namespace=None, box_id=None):
        """Backup all the namespaces registered."""
        return self.etcd.get_all()
