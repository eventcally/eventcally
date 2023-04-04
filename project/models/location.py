from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, Numeric, Unicode, and_
from sqlalchemy.event import listens_for

from project import db
from project.models.trackable_mixin import TrackableMixin


class Location(db.Model, TrackableMixin):
    __tablename__ = "location"
    id = Column(Integer(), primary_key=True)
    street = Column(Unicode(255))
    postalCode = Column(Unicode(255))
    city = Column(Unicode(255))
    state = Column(Unicode(255))
    country = Column(Unicode(255))
    latitude = Column(Numeric(18, 16))
    longitude = Column(Numeric(19, 16))
    coordinate = Column(Geometry(geometry_type="POINT"))

    def __init__(self, **kwargs):
        super(Location, self).__init__(**kwargs)

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


@listens_for(Location, "before_insert")
@listens_for(Location, "before_update")
def update_location_coordinate(mapper, connect, self):
    self.update_coordinate()
