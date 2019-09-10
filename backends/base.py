"""Base for all the Backend options for the Storehouse NApp."""


class StoreBase:
    """Base class for all the backend classes.

    Define the necessary methods for those classes.
    """

    def create(self, box):
        """Create a new box."""
        raise NotImplementedError

    def retrieve(self, namespace, box_id):
        """Retrieve a box from a namespace."""
        raise NotImplementedError

    def delete(self, namespace, box_id):
        """Delete a box from a namespace."""
        raise NotImplementedError

    def list(self, namespace):
        """List all the boxes in a namespace."""
        raise NotImplementedError

    def list_namespaces(self):
        """List all the namespaces registered."""
        raise NotImplementedError

    def backup(self, namespace, box_id):
        """Backup one or all the namespaces registered."""
        raise NotImplementedError
