from typing import List, Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.event_read_model import (
    EventDateDefinitionReadModel,
)
from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.domain.models.enums.event_status import EventStatus
from project.domain.types.changed_value import ChangedValue


class EventChangeSummaryReadModel(BaseReadModel):
    """The changes of an event that a referencing organization is notified about.

    Values stay raw (names, enums, bools, datetimes): the mail body is rendered once
    per recipient locale, so translating here would leak the first locale to everyone.

    ``organizer`` and ``event_place`` carry the *resolved names*. ``None`` means the
    id could not be resolved any more, i.e. the organizer or place was deleted --
    ``organizer_id`` and ``event_place_id`` on the domain event are never ``None``
    themselves. Should either become optional, this placeholder needs to be split.
    """

    model_config = ConfigDict(frozen=True)

    name: Optional[ChangedValue[str]] = None
    status: Optional[ChangedValue[EventStatus]] = None
    attendance_mode: Optional[ChangedValue[Optional[EventAttendanceMode]]] = None
    booked_up: Optional[ChangedValue[Optional[bool]]] = None
    organizer: Optional[ChangedValue[Optional[str]]] = None
    event_place: Optional[ChangedValue[Optional[str]]] = None
    date_definitions: Optional[ChangedValue[List[EventDateDefinitionReadModel]]] = None

    def has_changes(self) -> bool:
        return any(
            getattr(self, field_name) is not None
            for field_name in type(self).model_fields
        )
