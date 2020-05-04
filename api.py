"""Module to handle the storehouse."""
from kytos.core import log
from kytos.core.events import KytosEvent


class API:
    """Class to handle storehouse."""

    @classmethod
    def __new__(cls, *args, **kwargs):
        # pylint: disable=unused-argument
        """Make this class a Singleton."""
        instance = cls.__dict__.get("__instance__")
        if instance is not None:
            return instance
        cls.__instance__ = instance = object.__new__(cls)
        return instance

    def __init__(self, controller, namespace):
        """Create a storehouse instance."""
        self.controller = controller
        self.namespace = namespace
        self.list_stored_boxes()
        if 'box' not in self.__dict__:
            self.box = None

    def get_data(self):
        """Return the box data."""
        if not self.box:
            return {}
        self.get_stored_box(self.box.box_id)
        return self.box.data

    def create_box(self):
        """Create a new box."""
        content = {'namespace': self.namespace,
                   'callback': self._create_box_callback,
                   'data': {}}
        event = KytosEvent(name='kytos.storehouse.create', content=content)
        self.controller.buffers.app.put(event)
        log.info('Create box from storehouse.')

    def _create_box_callback(self, _event, data, error):
        """Execute the callback to handle create_box."""
        if error:
            log.error(f'Can\'t create box with namespace {self.namespace}')

        self.box = data
        log.info(f'Box {self.box.box_id} was created in {self.namespace}.')

    def list_stored_boxes(self):
        """List all boxes using the current namespace."""
        name = 'kytos.storehouse.list'
        content = {'namespace': self.namespace,
                   'callback': self._get_or_create_a_box_from_list_of_boxes}

        event = KytosEvent(name=name, content=content)
        self.controller.buffers.app.put(event)
        log.debug(f'Bootstraping storehouse box for {self.namespace}.')

    def _get_or_create_a_box_from_list_of_boxes(self, _event, data, _error):
        """Create a new box or retrieve the stored box."""
        if data:
            self.get_stored_box(data[0])
        else:
            self.create_box()

    def get_stored_box(self, box_id):
        """Get box from storehouse."""
        content = {'namespace': self.namespace,
                   'callback': self._get_box_callback,
                   'box_id': box_id,
                   'data': {}}
        name = 'kytos.storehouse.retrieve'
        event = KytosEvent(name=name, content=content)
        self.controller.buffers.app.put(event)
        log.debug(f'Retrieve box with {box_id} from {self.namespace}.')

    def _get_box_callback(self, _event, data, error):
        """Handle get_box method saving the box or logging with the error."""
        if error:
            log.error(f'Box {data.box_id} not found in {self.namespace}.')

        self.box = data
        log.debug(f'Box {self.box.box_id} was load from storehouse.')

    def save_data(self, data):
        """Save data in storehouse."""
        self.box.data[data.id] = data.as_dict()

        content = {'namespace': self.namespace,
                   'box_id': self.box.box_id,
                   'data': self.box.data,
                   'callback': self._save_data_callback}

        event = KytosEvent(name='kytos.storehouse.update', content=content)
        self.controller.buffers.app.put(event)

    def _save_data_callback(self, _event, data, error):
        """Display the data save result in the log."""
        if error:
            log.error(f'Can\'t update the {self.box.box_id}')

        log.info(f'Box {data.box_id} was updated.')
