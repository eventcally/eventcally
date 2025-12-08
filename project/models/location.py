from sqlalchemy import and_
from sqlalchemy.event import listens_for

from project import db
from project.models.iowned import IOwned
from project.models.location_generated import LocationGeneratedMixin


class Location(db.Model, LocationGeneratedMixin, IOwned):
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
