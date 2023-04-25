from sqlalchemy import Column, Integer, String, Unicode, UnicodeText, UniqueConstraint

from project import db
from project.models.trackable_mixin import TrackableMixin


class EventPlace(db.Model, TrackableMixin):
    __tablename__ = "eventplace"
    __table_args__ = (UniqueConstraint("name", "admin_unit_id"),)
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
