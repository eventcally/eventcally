from sqlalchemy import (
    Column,
    Integer,
    String,
    Unicode,
    UnicodeText,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.ext.hybrid import hybrid_property

from project import db
from project.models.event import Event
from project.models.trackable_mixin import TrackableMixin


class EventPlace(db.Model, TrackableMixin):
    __tablename__ = "eventplace"
    __table_args__ = (UniqueConstraint("name", "admin_unit_id"),)
    __display_name__ = "Place"
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id"))
    location = db.relationship(
        "Location",
        uselist=False,
        single_parent=True,
        cascade="all, delete-orphan",
        back_populates="eventplace",
    )
    photo_id = db.Column(db.Integer, db.ForeignKey("image.id"))
    photo = db.relationship(
        "Image",
        uselist=False,
        single_parent=True,
        cascade="all, delete-orphan",
        back_populates="eventplace",
    )
    url = Column(String(255))
    description = Column(UnicodeText())
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=True)

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
