from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.hybrid import hybrid_property

from project import db
from project.domain.commands import (
    CreateEventPlaceCommand,
    DeleteEventPlaceCommand,
    UpdateEventPlaceCommand,
)
from project.domain.events import (
    EventPlaceCreated,
    EventPlaceDeleted,
    EventPlaceUpdated,
)
from project.models.event import Event
from project.models.event_place_generated import EventPlaceGeneratedMixin


class EventPlace(db.Model, EventPlaceGeneratedMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def create(cls, cmd: CreateEventPlaceCommand) -> EventPlace:
        from project.models import Image, Location

        instance = cls()

        instance.admin_unit_id = cmd.admin_unit_id
        instance.name = cmd.name
        instance.url = cmd.url
        instance.description = cmd.description

        event = EventPlaceCreated(
            actor=cmd.actor,
            id=-1,
            admin_unit_id=instance.admin_unit_id,
            name=instance.name,
            url=instance.url,
            description=instance.description,
        )

        Location.create(cmd.location, instance, event, "location")
        Image.create(cmd.photo, instance, event, "photo")

        instance.domain_events.append(event)
        return instance

    def update(self, cmd: UpdateEventPlaceCommand):
        from project.models import Image, Location

        event = EventPlaceUpdated(actor=cmd.actor, id=self.id)

        self._update_field(cmd, event, "name")
        self._update_field(cmd, event, "url")
        self._update_field(cmd, event, "description")

        Location.update(cmd.location, self, event, "location")
        Image.update(cmd.photo, self, event, "photo")

        if event.has_changed_values():
            self.domain_events.append(event)

    def delete(self, cmd: DeleteEventPlaceCommand):
        self.domain_events.append(EventPlaceDeleted(actor=cmd.actor, id=self.id))

    @hybrid_property
    def number_of_events(self):
        return len(self.events)

    @number_of_events.expression
    def number_of_events(cls):
        return (
            select(func.count()).where(Event.event_place_id == cls.id).scalar_subquery()
        )

    def __str__(self):
        return self.name or super().__str__()
