from enum import IntEnum
from flask_security import AsaList
from geoalchemy2 import Geometry
from project import db
from sqlalchemy import (
    Index,
    Boolean,
    DateTime,
    Column,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Unicode,
    UniqueConstraint,
    ForeignKey,
    UnicodeText,
    CheckConstraint,
    cast,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import backref, deferred, relationship, remote
from sqlalchemy_utils import ColorType
import datetime
from project.dbtypes import IntegerEnum
from sqlalchemy.ext.declarative import declared_attr
from project.models.mixins.trackable_mixin import TrackableMixin


class EventOrganizerGeneratedMixin(TrackableMixin):
    __tablename__ = "eventorganizer"
    __table_args__ = (UniqueConstraint("name", "admin_unit_id"),)

    __model_name__ = "event_organizer"
    __model_name_plural__ = "event_organizers"
    __display_name__ = "Event organizer"
    __display_name_plural__ = "Event organizers"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def name(cls):
        return Column(Unicode(255), nullable=False)

    @declared_attr
    def url(cls):
        return deferred(Column(Unicode(255), nullable=True), group="detail")

    @declared_attr
    def email(cls):
        return deferred(Column(Unicode(255), nullable=True), group="detail")

    @declared_attr
    def phone(cls):
        return deferred(Column(Unicode(255), nullable=True), group="detail")

    @declared_attr
    def fax(cls):
        return deferred(Column(Unicode(255), nullable=True), group="detail")

    @declared_attr
    def location_id(cls):
        return Column(
            Integer(), ForeignKey("location.id", ondelete="SET NULL"), nullable=True
        )

    @declared_attr
    def logo_id(cls):
        return Column(
            Integer(), ForeignKey("image.id", ondelete="SET NULL"), nullable=True
        )

    @declared_attr
    def admin_unit_id(cls):
        return Column(
            Integer(), ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def location(cls):
        return relationship(
            "Location",
            foreign_keys=[cls.location_id],
            uselist=False,
            single_parent=True,
            cascade="all, delete-orphan",
            back_populates="event_organizer",
        )

    @declared_attr
    def logo(cls):
        return relationship(
            "Image",
            foreign_keys=[cls.logo_id],
            uselist=False,
            single_parent=True,
            cascade="all, delete-orphan",
            back_populates="event_organizer",
        )

    @declared_attr
    def admin_unit(cls):
        return relationship(
            "AdminUnit",
            foreign_keys=[cls.admin_unit_id],
            back_populates="event_organizers",
        )

    @declared_attr
    def events(cls):
        return relationship(
            "Event",
            back_populates="organizer",
            primaryjoin="Event.organizer_id == EventOrganizer.id",
        )

    @declared_attr
    def co_organized_events(cls):
        return relationship(
            "Event",
            back_populates="co_organizers",
            secondary="event_coorganizers",
        )
