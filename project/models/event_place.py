from sqlalchemy import Column, Integer, String, Unicode, UnicodeText, UniqueConstraint
from sqlalchemy.event import listens_for

from project import db
from project.models.trackable_mixin import TrackableMixin


class EventPlace(db.Model, TrackableMixin):
    __tablename__ = "eventplace"
    __table_args__ = (UniqueConstraint("name", "admin_unit_id"),)
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id"))
    location = db.relationship(
        "Location", uselist=False, single_parent=True, cascade="all, delete-orphan"
    )
    photo_id = db.Column(db.Integer, db.ForeignKey("image.id"))
    photo = db.relationship(
        "Image", uselist=False, single_parent=True, cascade="all, delete-orphan"
    )
    url = Column(String(255))
    description = Column(UnicodeText())
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=True)


@listens_for(EventPlace, "before_insert")
@listens_for(EventPlace, "before_update")
def purge_event_place(mapper, connect, self):
    if self.location and self.location.is_empty():
        self.location_id = None
    if self.photo and self.photo.is_empty():
        self.photo_id = None
