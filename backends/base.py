"""Base for all the Backend options for the Storehouse NApp."""
from abc import ABC


class StoreBase(ABC):
    """Abstract Base Class for all the backend classes.

    Define the necessary methods for those classes.
    """

    def create(self, box):
        """Create a new box."""

    def retrieve(self, namespace, box_id):
        """Retrieve a box from a namespace."""

    def delete(self, namespace, box_id):
        """Delete a box from a namespace."""

    def list(self, namespace):
        """List all the boxes in a namespace."""

    def list_namespaces(self):
        """List all the namespaces registered."""

    def backup(self, namespace, box_id):
        """Backup one or all the namespaces registered."""
