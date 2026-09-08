from typing import Optional

from project.application.read_models.event_change_summary_read_model import (
    EventChangeSummaryReadModel,
)
from project.application.read_models.event_read_model import (
    EventDateDefinitionReadModel,
)
from project.application.read_repositories.abstract_event_read_repository import (
    AbstractEventReadRepository,
)
from project.domain import events
from project.domain.types.changed_value import ChangedValue
from project.domain.types.object_id import ObjectId

# Single source of truth: which changes notify a referencing organization, and which
# summary field each of them ends up in. The gate and the rendered diff both derive
# from this mapping so they cannot drift apart -- a mail without a visible diff would
# be the result.
SIGNIFICANT_FIELDS = {
    "name": "name",
    "status": "status",
    "attendance_mode": "attendance_mode",
    "booked_up": "booked_up",
    "event_place_id": "event_place",
    "organizer_id": "organizer",
    "date_definitions": "date_definitions",
}


class EventChangeSummaryService:
    def __init__(self, event_read_repo: AbstractEventReadRepository):
        self.event_read_repo = event_read_repo

    def has_significant_changes(self, event: events.EventUpdated) -> bool:
        """Cheap in-memory gate. Deliberately performs no queries."""
        return any(
            getattr(event, field_name) is not None
            for field_name in SIGNIFICANT_FIELDS.keys()
        )

    def build(self, event: events.EventUpdated) -> EventChangeSummaryReadModel:
        organizer_names = self.event_read_repo.get_organizer_names(
            self._collect_ids(event.organizer_id)
        )
        place_names = self.event_read_repo.get_place_names(
            self._collect_ids(event.event_place_id)
        )

        return EventChangeSummaryReadModel(
            name=event.name,
            status=event.status,
            attendance_mode=event.attendance_mode,
            booked_up=event.booked_up,
            organizer=self._map_names(event.organizer_id, organizer_names),
            event_place=self._map_names(event.event_place_id, place_names),
            date_definitions=self._map_date_definitions(event.date_definitions),
        )

    def _collect_ids(
        self, changed_value: Optional[ChangedValue[ObjectId]]
    ) -> set[ObjectId]:
        if changed_value is None:
            return set()

        return {changed_value.old, changed_value.new}

    def _map_names(
        self,
        changed_value: Optional[ChangedValue[ObjectId]],
        names: dict[ObjectId, str],
    ) -> Optional[ChangedValue[Optional[str]]]:
        if changed_value is None:
            return None

        # A missing name means the organizer or place was deleted in the meantime.
        return ChangedValue(
            old=names.get(changed_value.old),
            new=names.get(changed_value.new),
        )

    def _map_date_definitions(
        self, changed_value
    ) -> Optional[ChangedValue[list[EventDateDefinitionReadModel]]]:
        if changed_value is None:
            return None

        return ChangedValue(
            old=[self._to_date_definition(d) for d in changed_value.old],
            new=[self._to_date_definition(d) for d in changed_value.new],
        )

    def _to_date_definition(self, value_object) -> EventDateDefinitionReadModel:
        return EventDateDefinitionReadModel(
            start=value_object.start,
            end=value_object.end,
            allday=value_object.allday,
            recurrence_rule=value_object.recurrence_rule,
        )
