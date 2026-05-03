from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.hybrid import hybrid_property

from project.domain.commands import (
    CreateEventOrganizerCommand,
    DeleteEventOrganizerCommand,
    UpdateEventOrganizerCommand,
)
from project.domain.events import (
    EventOrganizerCreated,
    EventOrganizerDeleted,
    EventOrganizerUpdated,
)
from project.extensions import db
from project.models.association_tables.event_co_organizers_generated import (
    EventCoOrganizersGeneratedMixin,
)
from project.models.event_organizer_generated import EventOrganizerGeneratedMixin


class EventOrganizer(db.Model, EventOrganizerGeneratedMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def create(cls, cmd: CreateEventOrganizerCommand) -> EventOrganizer:
        from project.models import Image, Location

        instance = cls()

        instance.admin_unit_id = cmd.admin_unit_id
        instance.name = cmd.name
        instance.url = cmd.url
        instance.email = cmd.email
        instance.phone = cmd.phone
        instance.fax = cmd.fax

        event = EventOrganizerCreated(
            actor=cmd.actor,
            id=-1,
            admin_unit_id=instance.admin_unit_id,
            name=instance.name,
            url=instance.url,
            email=instance.email,
            phone=instance.phone,
            fax=instance.fax,
        )

        Location.create(cmd.location, instance, event, "location")
        Image.create(cmd.logo, instance, event, "logo")

        instance.domain_events.append(event)
        return instance

    def update(self, cmd: UpdateEventOrganizerCommand):
        from project.models import Image, Location

        event = EventOrganizerUpdated(
            actor=cmd.actor, id=self.id, admin_unit_id=self.admin_unit_id
        )

        self._update_field(cmd, event, "name")
        self._update_field(cmd, event, "url")
        self._update_field(cmd, event, "email")
        self._update_field(cmd, event, "phone")
        self._update_field(cmd, event, "fax")

        Location.update(cmd.location, self, event, "location")
        Image.update(cmd.logo, self, event, "logo")

        if event.has_changed_values():
            self.domain_events.append(event)

    def delete(self, cmd: DeleteEventOrganizerCommand):
        self.domain_events.append(
            EventOrganizerDeleted(
                actor=cmd.actor, id=self.id, admin_unit_id=self.admin_unit_id
            )
        )

    @hybrid_property
    def number_of_events(self):
        return len(self.events)

    @number_of_events.expression
    def number_of_events(cls):
        from project.models.event import Event

        return (
            select(func.count()).where(Event.organizer_id == cls.id).scalar_subquery()
        )

    def __str__(self):
        return self.name or super().__str__()


class EventCoOrganizers(db.Model, EventCoOrganizersGeneratedMixin):
    pass
