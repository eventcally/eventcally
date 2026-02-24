from __future__ import annotations

from typing import Optional

from sqlalchemy import and_
from sqlalchemy.event import listens_for

from project import db
from project.domain import events
from project.domain.commands import CreateLocation, UpdateLocation
from project.domain.events import LocationCreated, LocationUpdated
from project.domain.types import Unsetable, unset
from project.models.iowned import IOwned
from project.models.location_generated import LocationGeneratedMixin


class Location(db.Model, LocationGeneratedMixin, IOwned):

    @classmethod
    def create(
        cls,
        cmd: Optional[CreateLocation],
        parent,
        parent_event: events.Event,
        field_name: str,
        event_field_name: Optional[str] = None,
    ):
        if cmd is None:
            return

        if event_field_name is None:
            event_field_name = field_name

        instance = cls()
        instance.street = cmd.street
        instance.postalCode = cmd.postalCode
        instance.city = cmd.city
        instance.state = cmd.state
        instance.country = cmd.country
        instance.latitude = cmd.latitude
        instance.longitude = cmd.longitude
        setattr(parent, field_name, instance)

        event = LocationCreated(
            street=instance.street,
            postalCode=instance.postalCode,
            city=instance.city,
            state=instance.state,
            country=instance.country,
            latitude=instance.latitude,
            longitude=instance.longitude,
        )
        setattr(parent_event, event_field_name, event)

    @classmethod
    def update(
        cls,
        cmd: Unsetable[UpdateLocation],
        parent,
        parent_event: events.Event,
        field_name: str,
        event_field_name: Optional[str] = None,
    ):
        if cmd == unset:
            return

        if event_field_name is None:
            event_field_name = field_name

        instance = getattr(parent, field_name)

        if cmd is None:
            if instance is not None:
                setattr(parent, field_name, None)
                setattr(parent_event, event_field_name, None)
            return

        if instance is None:
            instance = cls()

        event = LocationUpdated()
        instance._update_field(cmd, event, "street")
        instance._update_field(cmd, event, "postalCode")
        instance._update_field(cmd, event, "city")
        instance._update_field(cmd, event, "state")
        instance._update_field(cmd, event, "country")
        instance._update_field(cmd, event, "latitude")
        instance._update_field(cmd, event, "longitude")

        setattr(parent, field_name, instance)

        if event.has_changed_values():
            setattr(parent_event, event_field_name, event)

    def is_empty(self):
        return (
            not self.street
            and not self.postalCode
            and not self.city
            and not self.state
            and not self.country
            and not self.latitude
            and not self.longitude
        )

    def update_coordinate(self):
        if self.latitude and self.longitude:
            point = "POINT({} {})".format(self.longitude, self.latitude)
            self.coordinate = point
        else:
            self.coordinate = None

    @classmethod
    def update_coordinates(cls):
        locations = Location.query.filter(
            and_(
                Location.latitude is not None,
                Location.latitude != 0,
                Location.coordinate is None,
            )
        ).all()

        for location in locations:  # pragma: no cover
            location.update_coordinate()

        db.session.commit()

    def before_flush(self, session, is_dirty):
        if self.is_empty():
            if self.admin_unit:
                self.admin_unit.location = None

            if self.event_place:
                self.event_place.location = None

            if self.event_organizer:
                self.event_organizer.location = None

            if is_dirty:
                session.delete(self)


@listens_for(Location, "before_insert")
@listens_for(Location, "before_update")
def update_location_coordinate(mapper, connect, self):
    self.update_coordinate()
