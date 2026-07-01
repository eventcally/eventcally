from project.application.abstract_event_dispatcher import AbstractEventDispatcher
from project.domain import events


class CeleryEventDispatcher(AbstractEventDispatcher):
    def dispatch(self, event: events.Event):
        from project.base_tasks import process_delayed_event_v2

        event_class_path = f"{event.__class__.__module__}.{event.__class__.__name__}"
        event_json = event.model_dump_json(exclude_unset=True)
        process_delayed_event_v2.delay(event_class_path, event_json)
