from typing import List

from project.domain.types import ObjectId

from .base import Command


class SetEventCalendarsCommand(Command):
    """Puts the event into exactly these calendars of the organization (other
    organizations' calendars are never touched)."""

    admin_unit_id: ObjectId
    event_id: ObjectId
    calendar_ids: List[ObjectId]
