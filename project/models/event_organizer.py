from sqlalchemy import Column, Integer, String, Unicode, UniqueConstraint, func, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import deferred

from project import db
from project.models.trackable_mixin import TrackableMixin


class EventOrganizer(db.Model, TrackableMixin):
    __tablename__ = "eventorganizer"
    __table_args__ = (UniqueConstraint("name", "admin_unit_id"),)
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False)
    url = deferred(Column(String(255)), group="detail")
    email = deferred(Column(Unicode(255)), group="detail")
    phone = deferred(Column(Unicode(255)), group="detail")
    fax = deferred(Column(Unicode(255)), group="detail")
    location_id = deferred(db.Column(db.Integer, db.ForeignKey("location.id")))
    location = db.relationship(
        "Location",
        uselist=False,
        single_parent=True,
        cascade="all, delete-orphan",
        back_populates="eventorganizer",
    )
    logo_id = deferred(db.Column(db.Integer, db.ForeignKey("image.id")))
    logo = db.relationship(
        "Image",
        uselist=False,
        single_parent=True,
        cascade="all, delete-orphan",
        back_populates="eventorganizer",
    )
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=True)

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


class EventCoOrganizers(db.Model):
    __tablename__ = "event_coorganizers"
    __table_args__ = (UniqueConstraint("event_id", "organizer_id"),)
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    organizer_id = db.Column(
        db.Integer, db.ForeignKey("eventorganizer.id"), nullable=False
    )
