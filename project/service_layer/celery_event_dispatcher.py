from project.domain import events
from project.service_layer.abstract_event_dispatcher import AbstractEventDispatcher


class CeleryEventDispatcher(AbstractEventDispatcher):
    def dispatch(self, event: events.Event):
        from project.base_tasks import process_delayed_event

        event_class_path = f"{event.__class__.__module__}.{event.__class__.__name__}"
        event_dict = event.model_dump()
        process_delayed_event.delay(event_class_path, event_dict)
